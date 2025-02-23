# background_process.py
import asyncio
import copy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.pickup_tIme import PickupDateTime
from irony.models.pyobjectid import PyObjectId
from irony.models.service_location import DeliveryTypeEnum, ServiceLocation
from irony.models.timeslot_volume import TimeslotVolume
from irony.services.whatsapp import user_whatsapp_service
from irony.util import utils, whatsapp_utils
from irony.util.message import Message

# --------------------------
# Constants & Configuration
# --------------------------

GEO_NEAR_RADIUS_DEFAULT = 2000  # meters
MAX_ORDER_REQUESTS = 25
MAX_RETRY_ATTEMPTS = 3

# --------------------------
# Helper Functions
# --------------------------


def _validate_order_configuration(order: Order) -> None:
    """Validate required order fields for processing.

    Args:
        order: Order to validate

    Raises:
        WhatsappException: If required fields are missing
    """
    if not order.location or not order.location.location or not order.services:
        logger.error(
            "Invalid order configuration - missing location/services",
            extra={"order_id": order.id},
        )
        raise WhatsappException(config.DEFAULT_ERROR_REPLY_MESSAGE)


def _build_geo_near_pipeline(order: Order) -> List[Dict[str, Any]]:
    """Construct aggregation pipeline for finding nearby service locations.

    Args:
        order: Order containing location data

    Returns:
        Complete MongoDB aggregation pipeline
    """
    geo_radius = (
        config.DB_CACHE.get("config", {})
        .get("geo_near_radius", {})
        .get("value", GEO_NEAR_RADIUS_DEFAULT)
    )

    return [
        {
            "$geoNear": {
                "key": "coords",
                "near": {
                    "type": "Point",
                    "coordinates": order.location.location.coordinates,  # type: ignore
                },
                "distanceField": "distance",
                "maxDistance": geo_radius,
                "spherical": True,
            }
        },
        {
            "$match": {
                "$expr": {"$gte": ["$range", "$distance"]},
                "service_ids": {"$all": [s.id for s in order.services]},  # type: ignore
                "time_slots": {"$in": [order.time_slot]},
            }
        },
        {
            "$lookup": {
                "from": "timeslot_volume",
                "localField": "_id",
                "foreignField": "service_location_id",
                "as": "timeslot_volumes",
            }
        },
        {
            "$group": {
                "_id": "$delivery_type",
                "documents": {"$push": "$$ROOT"},
            }
        },
        {"$sort": {"distance": 1}},
        {"$limit": MAX_ORDER_REQUESTS},
    ]


async def _handle_no_ironman_found(wa_id: str) -> None:
    """Notify user when no service locations are available.

    Args:
        wa_id: User's WhatsApp ID for communication
    """
    message_body = whatsapp_utils.get_reply_message(
        "new_order_no_ironman", message_type="text"
    )
    await Message(message_body).send_message(wa_id)


# ITER 2 : start


async def _process_order_batch(pending_orders: List[OrderRequest]) -> None:
    """Process a batch of pending order requests."""
    ironman_msg = whatsapp_utils.get_reply_message(
        "new_order_send_ironman_request",
        message_type="interactive",
        message_sub_type="reply",
    )

    updates = {"order_requests": [], "orders": [], "service_locations": []}

    tasks = []
    for order_request in pending_orders:
        task = _process_single_order(order_request, ironman_msg, updates)
        tasks.append(task)

    await asyncio.gather(*tasks)
    await _persist_batch_updates(updates)


async def _process_single_order(
    order_request: OrderRequest,
    message_template: Dict[str, Any],
    updates: Dict[str, List],
) -> None:
    """Process individual order request based on delivery type."""
    if order_request.delivery_type == DeliveryTypeEnum.DELIVERY:
        await _process_delivery_order(order_request, updates)
    else:
        await _process_self_pickup_order(order_request, message_template, updates)


async def _process_delivery_order(
    order_request: OrderRequest, updates: Dict[str, List]
) -> None:
    """Handle delivery-type order requests."""
    if not order_request.delivery_service_locations_ids:
        await _handle_no_delivery_ironman(order_request)
        updates["order_requests"].append(order_request.id)
        return

    clothes_count = cache.get_clothes_cta_count(order_request.order.count_range)
    updated = False

    for service_location in order_request.delivery_service_locations:
        for service_entry in service_location.service_ids:
            if _can_assign_delivery(service_entry, order_request, clothes_count):
                service_entry.assigned_pieces_today += clothes_count
                updates["service_locations"].append(
                    service_location.model_dump(
                        exclude_unset=True, exclude_defaults=True, by_alias=True
                    )
                )
                await _update_order_allotment(
                    order_request.order, service_location, False
                )
                updates["orders"].append(order_request.order)
                updated = True
                break
        if updated:
            break

    if updated:
        updates["order_requests"].append(order_request.id)


def _can_assign_delivery(
    service_entry: Dict[str, Any], order_request: OrderRequest, clothes_count: int
) -> bool:
    """Check if delivery can be assigned to service location."""
    return (
        service_entry.service_id == order_request.order.services[0].id
        and service_entry.assigned_pieces_today + clothes_count
        < service_entry.daily_piece_limit
    )


async def _process_self_pickup_order(
    order_request: OrderRequest,
    message_template: Dict[str, Any],
    updates: Dict[str, List],
) -> None:
    """Handle self-pickup order requests."""
    service_location = order_request.service_location
    message = _format_self_pickup_message(
        message_template, order_request, service_location
    )

    await Message(message).send_message(service_location.wa_id)
    updates["order_requests"].append(order_request.id)


def _format_self_pickup_message(
    template: Dict[str, Any],
    order_request: OrderRequest,
    service_location: ServiceLocation,
) -> Dict[str, Any]:
    """Format self-pickup message template."""
    message = copy.deepcopy(template)
    order = order_request.order

    replacements = {
        "{service_location_name}": getattr(
            service_location, "name", "Service Provider"
        ),
        "{dist}": f"{int(order_request.distance)} Meters",
        "{count}": config.DB_CACHE["call_to_action"]
        .get(order.count_range, {})
        .get("title", "NA"),
        "{time}": config.DB_CACHE["call_to_action"]
        .get(order.time_slot, {})
        .get("title", "N/A"),
        "{amount}": str(order.total_price),
    }

    message["interactive"]["body"]["text"] = _perform_replacements(
        message["interactive"]["body"]["text"], replacements
    )

    return _add_button_ids(message, order_request.id)


def _perform_replacements(text: str, replacements: Dict[str, str]) -> str:
    """Perform multiple string replacements on message text."""
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


async def _persist_batch_updates(updates: Dict[str, List]) -> None:
    """Persist all batch updates to database."""
    if updates["orders"]:
        await replace_documents_in_transaction("order", updates["orders"])

    if updates["service_locations"]:
        await replace_documents_in_transaction(
            "service_locations", updates["service_locations"]
        )

    if updates["order_requests"]:
        await db.order_request.update_many(
            {"_id": {"$in": updates["order_requests"]}}, {"$set": {"is_pending": False}}
        )


async def _handle_no_delivery_ironman(order_request: OrderRequest) -> None:
    """Handle case where no delivery service locations are available."""
    logger.info(f"No ironman found for order {order_request.order.id}")
    no_ironman_msg = whatsapp_utils.get_reply_message(
        "new_order_no_ironman", message_type="text"
    )
    user = await db.user.find_one({"wa_id": order_request.order.user_wa_id})
    await Message(no_ironman_msg).send_message(user["wa_id"])


def _build_order_lookup() -> Dict[str, Any]:
    """Construct order lookup pipeline stage."""
    return {
        "$lookup": {
            "from": "order",
            "localField": "order_id",
            "foreignField": "_id",
            "as": "order",
        }
    }


# ITER 2 : end

# ITER 3 : start


def _build_user_lookup() -> Dict[str, Any]:
    """Construct user lookup stage for aggregation pipelines.

    Returns:
        MongoDB $lookup stage configuration for user collection
    """
    return {
        "$lookup": {
            "from": "user",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user",
        }
    }


def _create_work_messages(
    orders: List[Order], template: Dict[str, Any]
) -> List[Message]:
    """Create formatted work order messages for service locations.

    Args:
        orders: List of Order objects to process
        template: Base message template from configuration

    Returns:
        List of prepared Message objects ready for sending
    """
    return [
        Message(_format_work_message(order, template, idx + 1)).send_message(
            order.service_location.wa_id
        )
        for idx, order in enumerate(orders)
    ]


def _format_work_message(
    order: Order, template: Dict[str, Any], sequence: int
) -> Dict[str, Any]:
    """Format work message template with order details."""
    message = copy.deepcopy(template)
    count = (
        config.DB_CACHE["call_to_action"].get(order.count_range, {}).get("title", "NA")
    )

    message["interactive"]["body"]["text"] = (
        template["interactive"]["body"]["text"]
        .replace("{sno}", str(sequence))
        .replace("{bag}", order.bag_id)
        .replace("{count}", str(count))
        .replace("{phone}", str(order.user.wa_id)[2:])
        .replace("{delivery_date}", order.delivery_date.strftime("%d-%b-%Y"))
    )

    return _add_button_ids(message, order.id)


# ITER 3 : end


# --------------------------
# Order Request Management
# --------------------------


async def create_ironman_order_requests(order: Order, wa_id: str) -> None:
    """Create order requests for nearby service locations based on order details.

    Args:
        order: Order object containing service requirements
        wa_id: WhatsApp ID for user communication

    Raises:
        RuntimeError: When no nearby service locations are found
    """
    try:
        _validate_order_configuration(order)

        pipeline = _build_geo_near_pipeline(order)
        service_locations = await db.service_locations.aggregate(pipeline).to_list()

        if not any(loc["documents"] for loc in service_locations):
            await _handle_no_ironman_found(wa_id)
            raise RuntimeError("No nearby service locations available")

        order_requests = await _process_service_locations(order, service_locations)
        await _persist_order_requests(order_requests)

    except Exception as e:
        logger.error("Failed to create order requests", exc_info=True)
        raise


async def _process_service_locations(
    order: Order, service_locations: List[Dict[str, Any]]
) -> List[OrderRequest]:
    """Process service locations into order requests.

    Args:
        order: Original order object
        service_locations: Raw service location data from DB

    Returns:
        List of formatted OrderRequest objects
    """
    order_requests = []
    trigger_time = datetime.now()

    for loc_group in service_locations:
        delivery_type = loc_group["_id"]
        locations = loc_group["documents"]

        if delivery_type == DeliveryTypeEnum.SELF_PICKUP:
            order_requests.extend(
                await _process_self_pickup(order, locations, trigger_time)
            )
        elif delivery_type == DeliveryTypeEnum.DELIVERY:
            order_requests.append(_process_delivery(order, locations, trigger_time))

    return order_requests


async def _process_self_pickup(
    order: Order, locations: List[Dict[str, Any]], trigger_time: datetime
) -> List[OrderRequest]:
    """Handle self-pickup service locations."""
    requests = []
    for idx, loc_data in enumerate(locations):
        location = ServiceLocation(**loc_data)
        if location.auto_accept:
            if await check_limit_and_allot_order(order, location, True):
                break
        else:
            request = OrderRequest(
                order_id=order.id,
                delivery_type=DeliveryTypeEnum.SELF_PICKUP,
                service_location_id=location.id,
                distance=location.distance,
                trigger_time=trigger_time + timedelta(minutes=idx),
                is_pending=True,
                try_count=0,
            )
            requests.append(request)
    return requests


def _process_delivery(
    order: Order, locations: List[Dict[str, Any]], trigger_time: datetime
) -> OrderRequest:
    """Handle delivery service locations."""
    location_ids = [ServiceLocation(**loc).id for loc in locations]
    return OrderRequest(
        order_id=order.id,
        delivery_type=DeliveryTypeEnum.DELIVERY,
        delivery_service_locations_ids=location_ids,
        trigger_time=trigger_time + timedelta(minutes=15),
        is_pending=True,
        try_count=0,
    )


async def _persist_order_requests(requests: List[OrderRequest]) -> None:
    """Save order requests to database."""
    if requests:
        result = await db.order_request.insert_many(
            [r.model_dump(exclude_defaults=True) for r in requests]
        )
        logger.info(
            f"Inserted {len(result.inserted_ids)} order requests",
            extra={"request_ids": result.inserted_ids},
        )


# --------------------------
# Order Processing Logic
# --------------------------


async def check_limit_and_allot_order(
    order: Order, service_location: ServiceLocation, auto_allot: bool = False
) -> bool:
    """Check service location capacity and assign order if possible.

    Returns:
        bool: True if order was successfully allotted
    """
    if not _validate_allotment_prerequisites(order, service_location):
        return False

    timeslot_volume = _find_matching_timeslot(order, service_location)
    if not timeslot_volume:
        return False

    clothes_count = cache.get_clothes_cta_count(order.count_range)
    if not _validate_capacity(timeslot_volume, order, clothes_count):
        return False

    await _update_timeslot_volume(timeslot_volume, clothes_count)
    await _update_order_allotment(order, service_location, auto_allot)
    await _send_confirmation_message(order)

    return True


def _validate_allotment_prerequisites(
    order: Order, service_location: ServiceLocation
) -> bool:
    """Validate required fields for order allotment."""
    return all(
        [
            order.time_slot,
            order.services,
            order.services[0].call_to_action_key,  # type: ignore
            service_location.timeslot_volumes,
        ]
    )


def _find_matching_timeslot(
    order: Order, service_location: ServiceLocation
) -> Optional[TimeslotVolume]:
    """Find matching timeslot volume for order."""
    pickup_date = order.pickup_date_time.start.strftime("%Y-%m-%d")
    return next(
        (
            tv
            for tv in service_location.timeslot_volumes
            if tv and tv.operation_date and pickup_date in str(tv.operation_date)
        ),
        None,
    )


def _validate_capacity(
    timeslot_volume: TimeslotVolume, order: Order, clothes_count: int
) -> bool:
    """Validate available capacity in timeslot volume."""
    timeslot = timeslot_volume.timeslot_distributions[order.time_slot]
    service_key = order.services[0].call_to_action_key
    service = timeslot_volume.services_distribution[service_key]

    return all(
        [
            timeslot.limit - timeslot.current >= clothes_count,
            service.limit - service.current >= clothes_count,
        ]
    )


async def _update_timeslot_volume(
    timeslot_volume: TimeslotVolume, clothes_count: int
) -> None:
    """Update timeslot volume in database."""
    timeslot_volume.current_clothes += clothes_count
    await db.timeslot_volume.replace_one(
        {"_id": timeslot_volume.id},
        timeslot_volume.model_dump(exclude={"id"}, exclude_defaults=True),
    )


async def _update_order_allotment(
    order: Order, service_location: ServiceLocation, auto_allot: bool
) -> None:
    """Update order record with allotment details."""
    order_status = whatsapp_utils.get_new_order_status(
        order.id, OrderStatusEnum.PICKUP_PENDING
    )
    order.service_location_id = service_location.id
    order.order_status.insert(0, order_status)
    order.updated_on = datetime.now()
    order.auto_alloted = auto_allot

    await db.order.replace_one(
        {"_id": order.id},
        order.model_dump(exclude={"id"}, exclude_defaults=True, by_alias=True),
    )


async def _send_confirmation_message(order: Order) -> None:
    """Send order confirmation to user."""
    message_body = whatsapp_utils.get_reply_message(
        "new_order_ironman_alloted", message_sub_type="text"
    )
    last_message_update = {
        "type": "ORDER_CONFIRMED",
        "order_id": order.id,
        "order_taken": True,
    }
    await Message(message_body).send_message(order.user_wa_id, last_message_update)


# --------------------------
# Scheduled Tasks
# --------------------------


async def send_pending_order_requests() -> None:
    """Process pending order requests and notify service locations."""
    current_time = datetime.now()
    pending_orders = await _fetch_pending_orders(current_time)

    if not pending_orders:
        logger.info("No pending orders found")
        return

    logger.info(f"Processing {len(pending_orders)} pending orders")
    await _process_order_batch(pending_orders)


async def _fetch_pending_orders(current_time: datetime) -> List[OrderRequest]:
    """Retrieve pending orders ready for processing."""
    pipeline = [
        {
            "$match": {
                "trigger_time": {"$lt": current_time},
                "is_pending": True,
                "try_count": {"$lt": MAX_RETRY_ATTEMPTS},
            }
        },
        _build_service_location_lookup(),
        _build_order_lookup(),
        {"$unwind": "$order"},
    ]

    results = await db.order_request.aggregate(pipeline).to_list(None)
    return [OrderRequest(**doc) for doc in results]


def _build_service_location_lookup() -> Dict[str, Any]:
    """Construct service location lookup pipeline stage."""
    return {
        "$lookup": {
            "from": "service_locations",
            "localField": "service_location_id",
            "foreignField": "_id",
            "as": "service_location",
        }
    }


# --------------------------
# Delivery Scheduling
# --------------------------


async def send_ironman_delivery_schedule() -> None:
    """Send scheduled delivery/pickup notifications to service locations."""
    logger.info("Starting delivery schedule processing")

    time_gap = config.DB_CACHE["config"]["delivery_schedule_time_gap"]["value"]
    current_plus_n = datetime.now() + timedelta(minutes=time_gap)
    trigger_time = current_plus_n.strftime("%H:%M")

    schedules = await _fetch_pending_schedules(
        trigger_time,
        group_filter="TIME_SLOT_ID",
        status_flag="is_delivery_schedule_pending",
    )

    if not schedules:
        logger.info("No delivery schedules to process")
        return

    await _process_delivery_schedules(schedules)


def _build_delivery_pipeline(schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Construct pipeline for delivery schedule processing."""
    return [
        {
            "$match": {
                "time_slot": schedule["key"],
                "order_status.0.status": {
                    "$in": [
                        OrderStatusEnum.PICKUP_PENDING,
                        OrderStatusEnum.DELIVERY_PENDING,
                    ]
                },
            }
        },
        _build_user_lookup(),
        {"$unwind": "$user"},
        _build_service_location_lookup(),
        {"$unwind": "$service_location"},
        {"$sort": {"distance": 1}},
        {
            "$group": {
                "_id": "$service_location_id",
                "documents": {"$push": "$$ROOT"},
            }
        },
    ]


async def _process_delivery_schedules(schedules: List[Dict[str, Any]]) -> None:
    """Process batch of delivery schedules."""
    collect_msg = whatsapp_utils.get_reply_message(
        "ironman_collect_order", "interactive"
    )
    drop_msg = whatsapp_utils.get_reply_message("ironman_drop_order", "interactive")

    for schedule in schedules:
        pipeline = _build_delivery_pipeline(schedule)
        locations = await db.order.aggregate(pipeline).to_list(None)

        tasks = []
        for loc_group in locations:
            orders = [Order(**doc) for doc in loc_group["documents"]]
            tasks.extend(_create_delivery_messages(orders, collect_msg, drop_msg))

        await asyncio.gather(*tasks)
        await _update_schedule_status(schedule["_id"], "is_delivery_schedule_pending")


def _create_delivery_messages(
    orders: List[Order], collect_template: Dict[str, Any], drop_template: Dict[str, Any]
) -> List[Message]:
    """Create formatted messages for delivery orders."""
    messages = []
    for idx, order in enumerate(orders):
        template = (
            collect_template
            if order.order_status[0].status == OrderStatusEnum.PICKUP_PENDING
            else drop_template
        )
        message = _format_delivery_message(order, template, idx + 1)
        messages.append(Message(message).send_message(order.service_location.wa_id))
    return messages


def _format_delivery_message(
    order: Order, template: Dict[str, Any], sequence: int
) -> Dict[str, Any]:
    """Format delivery message template with order details."""
    message = copy.deepcopy(template)
    count = (
        cache.get_clothes_cta_count(order.count_range)
        if order.order_status[0].status == OrderStatusEnum.PICKUP_PENDING
        else order.total_count
    )

    message["interactive"]["body"]["text"] = (
        template["interactive"]["body"]["text"]
        .replace("{sno}", str(sequence))
        .replace("{name}", order.user.name)
        .replace("{count}", str(count))
        .replace("{link}", utils.get_maps_link(order.location))
        .replace("{phone}", str(order.user.wa_id)[2:])
        .replace("{amount}", str(order.total_price))
    )
    return _add_button_ids(message, order.id)


# --------------------------
# Work Scheduling
# --------------------------


async def send_ironman_work_schedule() -> None:
    """Send work schedule notifications to service locations."""
    logger.info("Starting work schedule processing")

    time_gap = config.DB_CACHE["config"]["work_schedule_time_gap"]["value"]
    current_minus_n = datetime.now() - timedelta(minutes=time_gap)
    trigger_time = current_minus_n.strftime("%H:%M")

    schedules = await _fetch_pending_schedules(
        trigger_time, status_flag="is_work_schedule_pending"
    )

    if not schedules:
        logger.info("No work schedules to process")
        return

    await _process_work_schedules(schedules)
    await assign_missed_pickup_to_other_ironmans(schedules[0])


async def _process_work_schedules(schedules: List[Dict[str, Any]]) -> None:
    """Process batch of work schedules."""
    message_template = whatsapp_utils.get_reply_message(
        "ironman_to_work_order", "interactive"
    )

    for schedule in schedules:
        pipeline = _build_work_pipeline(schedule)
        locations = await db.order.aggregate(pipeline).to_list(None)

        tasks = []
        for loc_group in locations:
            orders = [Order(**doc) for doc in loc_group["documents"]]
            tasks.extend(_create_work_messages(orders, message_template))

        await asyncio.gather(*tasks)
        await _update_schedule_status(schedule["_id"], "is_work_schedule_pending")


def _build_work_pipeline(schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Construct pipeline for work schedule processing."""
    return [
        {
            "$match": {
                "time_slot": schedule["key"],
                "order_status.0.status": {
                    "$in": [
                        OrderStatusEnum.PICKUP_COMPLETE,
                        OrderStatusEnum.WORK_IN_PROGRESS,
                    ]
                },
            }
        },
        _build_user_lookup(),
        {"$unwind": "$user"},
        _build_service_location_lookup(),
        {"$unwind": "$service_location"},
        {"$sort": {"distance": 1}},
        {
            "$group": {
                "_id": "$service_location_id",
                "documents": {"$push": "$$ROOT"},
            }
        },
    ]


# --------------------------
# Shared Helper Functions
# --------------------------


async def _fetch_pending_schedules(
    trigger_time: str,
    group_filter: Optional[str] = None,
    status_flag: str = "is_pending",
) -> List[Dict[str, Any]]:
    """Retrieve pending schedules from database."""
    match_stage = {"start_time": {"$lte": trigger_time}, status_flag: True}
    if group_filter:
        match_stage["group"] = group_filter

    return await db.config.aggregate([{"$match": match_stage}]).to_list(None)


async def _update_schedule_status(schedule_id: PyObjectId, status_field: str) -> None:
    """Update schedule status in database."""
    await db.config.update_one({"_id": schedule_id}, {"$set": {status_field: False}})


def _add_button_ids(message: Dict[str, Any], order_id: PyObjectId) -> Dict[str, Any]:
    """Add order ID to interactive buttons in message template."""
    for button in message["interactive"]["action"]["buttons"]:
        button["reply"]["id"] = f"{button['reply']['id']}#{order_id}"
    return message


# --------------------------
# Missed Orders Handling
# --------------------------


async def assign_missed_pickup_to_other_ironmans(schedule: Dict[str, Any]) -> None:
    """Reassign orders with missed pickups to alternative service locations."""
    logger.info("Starting missed pickup reassignment")

    time_gap = config.DB_CACHE["config"]["missing_pickup_gap"]["value"]
    current_time = datetime.now() + timedelta(minutes=time_gap)
    start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    orders = await _fetch_missed_orders(start_of_day, current_time)
    if not orders:
        logger.info("No missed orders found")
        return

    time_slots = user_whatsapp_service.get_slots(
        [v for k, v in config.DB_CACHE["config"].items() if "TIME_SLOT_ID" in k],
        "start_time",
    )

    await _process_missed_orders(orders, time_slots)


async def _fetch_missed_orders(start_time: datetime, end_time: datetime) -> List[Order]:
    """Retrieve orders with missed pickups."""
    pipeline = [
        {
            "$match": {
                "order_status.0.status": OrderStatusEnum.PICKUP_PENDING,
                "pickup_date_time.end": {"$gte": start_time, "$lte": end_time},
            }
        }
    ]
    results = await db.order.aggregate(pipeline).to_list(None)
    return [Order(**doc) for doc in results]


async def _process_missed_orders(
    orders: List[Order], time_slots: Dict[str, Any]
) -> None:
    """Process batch of missed orders."""
    for order in orders:
        await _clear_pickup_status(order)
        next_slot = cache.get_next_time_slot(order.time_slot)

        if next_slot:
            await _update_order_time_slot(order, next_slot, time_slots)
            await create_ironman_order_requests(order, order.user_wa_id)


async def _clear_pickup_status(order: Order) -> None:
    """Remove pickup pending status from order history."""
    order.order_status = [
        status
        for status in order.order_status
        if status.status != OrderStatusEnum.PICKUP_PENDING
    ]
    await db.order.replace_one(
        {"_id": order.id},
        order.model_dump(exclude={"id"}, exclude_defaults=True, by_alias=True),
    )


async def _update_order_time_slot(
    order: Order, next_slot: Dict[str, Any], time_slots: Dict[str, Any]
) -> None:
    """Update order with new time slot information."""
    now = datetime.now()
    start_time = now.replace(
        hour=time_slots[next_slot["key"]]["start"].hour,
        minute=time_slots[next_slot["key"]]["start"].minute,
    )
    end_time = now.replace(
        hour=time_slots[next_slot["key"]]["end"].hour,
        minute=time_slots[next_slot["key"]]["end"].minute,
    )

    order.time_slot = next_slot["key"]
    order.pickup_date_time = PickupDateTime(start=start_time, end=end_time)
    order.updated_on = datetime.now()
    order.service_location_id = None
    order.auto_alloted = None

    await db.order.update_one(
        {"_id": order.id},
        {
            "$set": order.model_dump(
                exclude={"id"}, exclude_defaults=True, by_alias=True
            )
        },
    )


# --------------------------
# Main Execution Guard
# --------------------------

if __name__ == "__main__":
    # Initialize async event loop for scheduled tasks
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_pending_order_requests())
    finally:
        loop.close()
