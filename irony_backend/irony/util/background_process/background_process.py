import asyncio
import copy
from datetime import datetime, timedelta
from typing import Any, Dict, List

import irony.util.whatsapp_utils as whatsapp_utils
from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.db import db
from irony.exception.WhatsappException import WhatsappException
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.pickup_tIme import PickupDateTime
from irony.models.pyobjectid import PyObjectId  # Add this import
from irony.models.service_location import ServiceLocation
from irony.models.timeslot_volume import TimeslotVolume
from irony.services.whatsapp import user_whatsapp_service
from irony.util import utils
from irony.util.background_process import pipelines
from irony.util.message import Message


# Helper : 1
def _validate_order(order: Order) -> None:
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


async def create_ironman_order_requests(order: Order, wa_id: str):
    try:
        _validate_order(order)

        geo_near_radius = (
            config.DB_CACHE.get("config", {})
            .get("geo_near_radius", {})
            .get("value", 2000)
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_geo_near_service_locations_for_order(
                order, geo_near_radius
            )
        )

        delivery_type_group_service_locations: List[Dict[str, Any]] = (
            await db.service_locations.aggregate(pipeline=pipeline).to_list(length=None)
        )

        if not any(
            loc_group["documents"]
            for loc_group in delivery_type_group_service_locations
        ):
            no_nearby_service_locations_message_body = whatsapp_utils.get_reply_message(
                "new_order_no_ironman", message_type="text"
            )
            await Message(no_nearby_service_locations_message_body).send_message(wa_id)
            raise RuntimeError("No nearby service locations available")

        order_requests: List[OrderRequest] = []
        trigger_time = datetime.now()

        for location_group in delivery_type_group_service_locations:
            delivery_type = location_group["_id"]
            service_locations = location_group["documents"]

            for index, service_location in enumerate(service_locations):
                service_location = ServiceLocation(**service_location)
                if service_location.auto_accept:
                    if await check_limit_and_allot_order(order, service_location, True):
                        await _send_order_confirmation_message(order, service_location)
                        return
                else:
                    trigger_time = trigger_time + timedelta(minutes=index * 1)
                    order_request = OrderRequest(
                        order_id=order.id,
                        delivery_type=delivery_type,
                        service_location_id=service_location.id,
                        distance=service_location.distance,
                        trigger_time=trigger_time,
                        is_pending=True,
                        try_count=0,
                    )
                    order_requests.append(order_request)

        order_requests.append(
            OrderRequest(
                order_id=order.id,
                trigger_time=trigger_time + timedelta(minutes=45),
                is_pending=True,
                try_count=0,
            )
        )
        if order_requests:
            result = await db.order_request.insert_many(
                [
                    order_request.model_dump(exclude_defaults=True)
                    for order_request in order_requests
                ]
            )

            logger.info(
                "Inserted %d rows. Into order_request collection. ids: %s",
                len(result.inserted_ids),
                result.inserted_ids,
            )
        # logger.info(f"Order assigned to ServiceLocation {temp_name}.")
    except (RuntimeError, WhatsappException):
        logger.error("Exception in find_ironman", exc_info=True)


async def _send_order_confirmation_message(order, service_location):
    message_body = whatsapp_utils.get_reply_message(
        message_key="new_order_ironman_alloted",
        message_sub_type="text",
    )

    utils.replace_message_keys_with_values(
        message_body,
        {
            "{service_location_name}": str(
                getattr(
                    service_location,
                    "name",
                    "Our Service Provider",
                )
            ),
            "{time}": config.DB_CACHE["call_to_action"]
            .get(order.time_slot, {})
            .get("title", "N/A"),
        },
    )

    last_message_update = {
        "type": "ORDER_CONFIRMED",
        "order_id": order.id,
        "order_taken": True,
    }

    logger.info("Sending message to user: %s", message_body)
    await Message(message_body).send_message(order.user_wa_id, last_message_update)


async def check_limit_and_allot_order(
    order: Order,
    service_location: ServiceLocation,
    auto_allot: bool = False,
):
    if (
        not order.time_slot
        or not order.services
        or not order.services[0].call_to_action_key
        or not service_location.timeslot_volumes
    ):
        return False

    timeslot_volume = _get_timeslot_volume_for_order(order, service_location)

    if (
        not timeslot_volume
        or not timeslot_volume.timeslot_distributions
        or not timeslot_volume.services_distribution
    ):
        return False

    timeslot_distribution = timeslot_volume.timeslot_distributions[order.time_slot]
    service_distribution = timeslot_volume.services_distribution[
        order.services[0].call_to_action_key
    ]

    clothes_count = cache.get_clothes_cta_count(order.count_range)
    if (
        timeslot_volume.daily_limit - timeslot_volume.current_clothes < clothes_count
        or timeslot_distribution.limit - timeslot_distribution.current < clothes_count
        or service_distribution.limit - service_distribution.current < clothes_count
    ):
        return False

    # Update timeslot volume
    timeslot_distribution.current += clothes_count
    service_distribution.current += clothes_count
    timeslot_volume.current_clothes += clothes_count

    await db.timeslot_volume.replace_one(
        {"_id": timeslot_volume.id},
        timeslot_volume.model_dump(exclude_defaults=True, exclude={"id"}),
    )

    # Update order
    order_status = whatsapp_utils.get_new_order_status(
        order.id, OrderStatusEnum.PICKUP_PENDING
    )
    order.order_status.insert(0, order_status)  # type: ignore
    order.service_location_id = service_location.id
    order.updated_on = datetime.now()
    if auto_allot:
        order.auto_alloted = True

    await db.order.replace_one(
        {"_id": order.id},
        order.model_dump(exclude_defaults=True, exclude={"id"}, by_alias=True),
    )

    return True


def _get_timeslot_volume_for_order(order: Order, service_location: ServiceLocation):
    timeslot_volume: TimeslotVolume | None = next(
        (
            timeslot_volume
            for timeslot_volume in service_location.timeslot_volumes  # type: ignore
            if timeslot_volume
            and timeslot_volume.operation_date
            and order.pickup_date_time
            and order.pickup_date_time.start
            and order.pickup_date_time.start.strftime("%Y-%m-%d")
            in str(timeslot_volume.operation_date)
            and timeslot_volume.timeslot_distributions
        ),
        None,
    )

    return timeslot_volume


async def send_pending_order_requests():
    logger.info("Started send_pending_order_requests")
    current_time = datetime.now()
    pipeline = pipelines.get_pipeline_pending_orders_requests(current_time)

    pending_order_request_docs = await db.order_request.aggregate(
        pipeline=pipeline
    ).to_list(None)

    if not pending_order_request_docs:
        logger.info("No pending orders found")
        return

    logger.info("Number of pending orders: %d", len(pending_order_request_docs))
    tasks = []
    order_request_updates = []
    message = whatsapp_utils.get_reply_message(
        "new_order_send_ironman_request",
        message_type="interactive",
        message_sub_type="reply",
    )

    for order_request_doc in pending_order_request_docs:
        order_request = OrderRequest(**order_request_doc)
        order = order_request.order
        # order_requests that dont have service_location_id are final one's that just trigger the final message(no ironman found) to user
        if not order_request.service_location_id:
            logger.info("No ironman found for order: %s", order.id)  # type: ignore
            order_request_updates.append(PyObjectId(str(order_request.id)))
            no_ironman_message = whatsapp_utils.get_reply_message(
                "new_order_no_ironman", message_type="text"
            )
            tasks.append(
                Message(no_ironman_message).send_message(
                    db.user.find_one({"wa_id": order.user_wa_id})  # type: ignore
                )
            )
            continue

        # Create a copy of message_doc for each iteration
        service_location = order_request.service_location
        message_copy = copy.deepcopy(message)
        _populate_order_request_message_fields(
            order_request, order, service_location, message_copy
        )
        tasks.append(Message(message_copy).send_message(service_location.wa_id))  # type: ignore
        order_request_updates.append(PyObjectId(str(order_request.id)))

    # Send all messsages at once
    await asyncio.gather(*tasks)

    if len(order_request_updates) > 0:
        await db.order_request.update_many(
            {"_id": {"$in": order_request_updates}},
            {"$set": {"is_pending": False}},
        )


def _populate_order_request_message_fields(
    order_request, order, service_location, message_copy
):
    message_copy["interactive"]["action"]["buttons"] = [
        {
            **button,
            "reply": {
                **button["reply"],
                "id": str(button["reply"]["id"]) + "#" + str(order_request.id),
            },
        }
        for button in message_copy["interactive"]["action"]["buttons"]
    ]

    message_copy["interactive"]["body"]["text"] = (
        str(message_copy["interactive"]["body"]["text"])
        .replace(
            "{service_location_name}",
            getattr(service_location, "name", "Service Provider"),
        )
        .replace(
            "{dist}",
            str(getattr(order_request, "distance", "NA")).split(".", maxsplit=1)[0]
            + " Meters",
        )
        .replace(
            "{count}",
            config.DB_CACHE["call_to_action"]
            .get(getattr(order, "count_range", "NA"), {})
            .get("title", "NA"),
        )
        .replace(
            "{time}",
            config.DB_CACHE["call_to_action"]
            .get(order_request.order.time_slot, {})  # type: ignore
            .get("title", "N/A"),
        )
        .replace("{amount}", str(getattr(order, "total_price", "NA")))
    )


async def send_ironman_delivery_schedule():
    logger.info("Started send_ironman_schedule")
    n = config.DB_CACHE["config"]["delivery_schedule_time_gap"]["value"]
    current_plus_n = datetime.now() + timedelta(minutes=n)
    trigger_time_str = f"{current_plus_n.hour:02d}:{current_plus_n.minute:02d}"

    pipeline = pipelines.get_pipeline_is_ironman_delivery_schedule_pending(
        trigger_time_str=trigger_time_str
    )

    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)
    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    logger.info("Number of pending schedules: %d", len(pending_schedules))

    collect_message = whatsapp_utils.get_reply_message(
        "ironman_collect_order",
        message_type="interactive",
        message_sub_type="reply",
    )

    drop_message = whatsapp_utils.get_reply_message(
        "ironman_drop_order", message_type="interactive", message_sub_type="reply"
    )

    for pending_schedule in pending_schedules:
        pipeline = pipelines.get_pipeline_ironman_delivery_schedule(
            pending_schedule_key=pending_schedule["key"]
        )
        service_location_grouped_orders = await db.order.aggregate(
            pipeline=pipeline
        ).to_list(None)

        for service_location_group in service_location_grouped_orders:
            tasks = []
            orders = service_location_group["documents"]

            for idx, order_doc in enumerate(orders):
                order = Order(**order_doc)

                message_copy = None
                count = None
                link = utils.get_maps_link(order.location)

                # This is currently put to restrict orders that are taken at service_location using order management system.
                # Later after adding seperate order type for "user drop/pickup at store" orders change this.
                if link is None:
                    continue

                if order.order_status[0].status == OrderStatusEnum.PICKUP_PENDING:
                    message_copy = copy.deepcopy(collect_message)
                    count = (
                        config.DB_CACHE["call_to_action"]
                        .get(getattr(order, "count_range", "NA"), {})
                        .get("title", "NA")
                    )
                else:
                    message_copy = copy.deepcopy(drop_message)
                    count = order.total_count

                _populate_delivery_schedule_message_fields(
                    idx, order, message_copy, count, link
                )

                # send message to ironman
                tasks.append(
                    Message(message_copy).send_message(order.service_location.wa_id)  # type: ignore
                )
            logger.info(
                "Sending messages to ironman for service location: %s",
                service_location_group["_id"],
            )
            await asyncio.gather(*tasks)

        # update schedule status
        await db.config.update_one(
            {"_id": pending_schedule["_id"]},
            {"$set": {"is_delivery_schedule_pending": False}},
        )

    logger.info("Completed send_ironman_schedule")


def _populate_delivery_schedule_message_fields(idx, order, message_copy, count, link):
    message_copy["interactive"]["action"]["buttons"] = [
        {
            **button,
            "reply": {
                **button["reply"],
                "id": str(button["reply"]["id"]) + "#" + str(order.id),
            },
        }
        for button in message_copy["interactive"]["action"]["buttons"]
    ]

    message_copy["interactive"]["body"]["text"] = (
        str(message_copy["interactive"]["body"]["text"])
        .replace("{sno}", str(idx + 1))
        .replace("{name}", getattr(order.user, "name", "Customer"))
        .replace("{count}", str(count))
        .replace(
            "{link}",
            link or "",
        )
        .replace("{phone}", str(order.user.wa_id)[2:])  # type: ignore
        .replace("{amount}", str(getattr(order, "total_price", "NA")))
    )


async def send_ironman_work_schedule():
    logger.info("Started send_ironman_schedule")
    logger.info("Finding pending pickup/drop orders")
    n = config.DB_CACHE["config"]["work_schedule_time_gap"]["value"]
    current_minus_n = datetime.now() - timedelta(minutes=n)
    trigger_time = f"{current_minus_n.hour:02d}:{current_minus_n.minute:02d}"

    pipeline = pipelines.get_pipeline_is_work_schedule_pending(
        trigger_time=trigger_time
    )

    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)
    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    logger.info("Number of pending schedules: %d", len(pending_schedules))

    for pending_schedule in pending_schedules:
        pipeline = pipelines.get_pipeline_ironman_work_schedule(
            pending_schedule_key=pending_schedule["key"]
        )
        service_location_orders = await db.order.aggregate(pipeline=pipeline).to_list(
            None
        )

        message = whatsapp_utils.get_reply_message(
            "ironman_to_work_order",
            message_type="interactive",
            message_sub_type="reply",
        )

        for service_location_order in service_location_orders:
            tasks = []
            orders = service_location_order["documents"]

            for i, order in enumerate(orders):
                order = Order(**order)

                message_copy = None
                count = None

                message_copy = copy.deepcopy(message)
                count = (
                    config.DB_CACHE["call_to_action"]
                    .get(getattr(order, "count_range", "NA"), {})
                    .get("title", "NA")
                )

                _populate_send_agent_work_schedule_message(
                    i, order, message_copy, count
                )

                # send message to ironman
                tasks.append(
                    Message(message_copy).send_message(order.service_location.wa_id)  # type: ignore
                )
            logger.info(
                "Sending messages to ironman for service location: %s",
                service_location_order["_id"],
            )
            await asyncio.gather(*tasks)

        # update schedule status
        await db.config.update_one(
            {"_id": pending_schedule["_id"]},
            {"$set": {"is_work_schedule_pending": False}},
        )

    logger.info("Completed send_ironman_schedule")


def _populate_send_agent_work_schedule_message(i, order, message_copy, count):
    message_copy["interactive"]["action"]["buttons"] = [
        {
            **button,
            "reply": {
                **button["reply"],
                "id": str(button["reply"]["id"]) + "#" + str(order.id),
            },
        }
        for button in message_copy["interactive"]["action"]["buttons"]
    ]

    message_copy["interactive"]["body"]["text"] = (
        str(message_copy["interactive"]["body"]["text"])
        .replace("{sno}", str(i + 1))
        .replace("{bag}", "LOL")
        .replace("{count}", str(count))
        .replace("{phone}", str(order.user.wa_id)[2:])
        .replace("{delivery_date}", str(getattr(order, "delivery_date", "NA")))
    )


async def send_ironman_pending_work_schedule():
    logger.info("Started send_ironman_schedule")
    n = config.DB_CACHE["config"]["pending_schedule_time_gap"]["value"]
    current_minus_n = datetime.now() + timedelta(minutes=n)
    trigger_time = f"{current_minus_n.hour:02d}:{current_minus_n.minute:02d}"

    pipeline = pipelines.get_pipeline_is_pending_work_schedule_pending(trigger_time)

    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)
    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    logger.info("Number of pending schedules: %d", len(pending_schedules))

    for pending_schedule in pending_schedules:
        # Get the current date
        current_date = datetime.now().date()

        # Combine the date and time
        start_datetime = datetime.strptime(
            f"{current_date} {pending_schedule['start_time']}", "%Y-%m-%d %H:%M"
        )
        end_datetime = datetime.strptime(
            f"{current_date} {pending_schedule['end_time']}", "%Y-%m-%d %H:%M"
        )

        pipeline = pipelines.get_pipeline_pending_work_schedule(
            pending_schedule["key"], start_datetime, end_datetime
        )

        service_location_orders = await db.order.aggregate(pipeline=pipeline).to_list(
            None
        )

        message = whatsapp_utils.get_reply_message(
            "ironman_pending_to_work_order",
            message_type="interactive",
            message_sub_type="reply",
        )

        for service_location_order in service_location_orders:
            tasks = []
            orders = service_location_order["documents"]

            for i, order in enumerate(orders):
                order = Order(**order)

                message_copy = None
                count = None

                message_copy = copy.deepcopy(message)
                count = (
                    config.DB_CACHE["call_to_action"]
                    .get(getattr(order, "count_range", "NA"), {})
                    .get("title", "NA")
                )

                _populate_send_agent_work_schedule_message(
                    i, order, message_copy, count
                )

                # send message to ironman
                tasks.append(
                    Message(message_copy).send_message(order.service_location.wa_id)  # type: ignore
                )
            logger.info(
                "Sending messages to ironman for service location: %s",
                service_location_order["_id"],
            )
            await asyncio.gather(*tasks)

        # update schedule status
        await db.config.update_one(
            {"_id": pending_schedule["_id"]},
            {"$set": {"is_pending_schedule_pending": False}},
        )

    logger.info("Completed send_ironman_schedule")


async def create_timeslot_volume_record():
    is_timeslot_volumene_archive_pending_key = "is_timeslot_volume_archive_pending"
    archive_status_doc = await db.config.find_one(
        {"key": is_timeslot_volumene_archive_pending_key, "value": True}
    )

    if not archive_status_doc:
        logger.info("Timeslot volume records already archived.")
        return

    source_collection = db["timeslot_volume"]
    archive_collection = db["timeslot_volume_arch"]

    today = datetime.now()
    yesterday = today - timedelta(days=1)
    start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_of_yesterday = start_of_yesterday + timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    active_service_locations: List[ServiceLocation] = []
    async for service_location in db.service_locations.find({"is_active": True}):
        active_service_locations.append(ServiceLocation(**service_location))

    pipeline = pipelines.get_pipeline_timeslot_volume_archive(end_of_yesterday)
    records_found = await source_collection.aggregate(pipeline).to_list(length=None)
    records_to_archive: List[TimeslotVolume] = [
        TimeslotVolume(**record) for record in records_found
    ]
    # records_to_archive_timeslot_volume: List[TimeslotVolume] = []

    tomorrow_records: List[TimeslotVolume] = []
    # Create records for tomorrow for all active service locations
    for service_location in active_service_locations:
        new_timeslot_volume = TimeslotVolume(daily_limit=service_location.daily_limit, current_clothes=0)  # type: ignore
        new_timeslot_volume.operation_date = tomorrow
        new_timeslot_volume.service_location_id = service_location.id
        new_timeslot_volume.timeslot_distributions = (
            service_location.timeslot_distributions  # type: ignore
        )
        new_timeslot_volume.services_distribution = (
            service_location.services_distribution  # type: ignore
        )
        tomorrow_records.append(new_timeslot_volume)

    if records_to_archive:
        archive_result = await archive_collection.insert_many(
            [
                records_to_archive_timeslot_volume.model_dump(exclude_unset=True)
                for records_to_archive_timeslot_volume in records_to_archive
            ]
        )
        result = await source_collection.delete_many(
            {"operation_date": {"$lt": end_of_yesterday}}
        )

        logger.info(
            "Archived %d records and deleted them from source collection",
            len(archive_result.inserted_ids),
        )
        logger.info("Deleted %d records from source collection", result.deleted_count)

    if tomorrow_records:
        result = await source_collection.insert_many(
            [
                tomorrow_record.model_dump(exclude_unset=True)
                for tomorrow_record in tomorrow_records
            ]
        )

        logger.info(
            "Inserted %d records for tomorrow in source collection",
            len(result.inserted_ids),
        )

    await db.config.update_one(
        {"key": is_timeslot_volumene_archive_pending_key}, {"$set": {"value": False}}
    )
    logger.info("Completed create_timeslot_volume_record and archived the records.")


async def create_order_requests():
    current_time = datetime.now()
    pipeline = pipelines.get_pipeline_pending_orders_create_requests(current_time)

    pending_orders = await db.order.aggregate(pipeline=pipeline).to_list(None)
    if not pending_orders:
        logger.info("No pending orders to create order requests")
        return

    logger.info("Number of pending orders: %d", len(pending_orders))
    tasks = []
    order_ids = []
    for i in pending_orders:
        order = Order(**i)
        order_ids.append(order.id)
        tasks.append(create_ironman_order_requests(order, order.user_wa_id))  # type: ignore

    await db.order.update_many(
        {"_id": {"$in": order_ids}},
        {"$set": {"trigger_order_request_pending": False}},
    )

    await asyncio.gather(*tasks)

    logger.info("Completed create_order_requests")


async def reassign_missed_orders():
    logger.info("Started reassign_missed_orders")
    n = config.DB_CACHE["config"]["missing_pickup_gap"]["value"]

    current_time = datetime.now() + timedelta(minutes=n)
    start_of_today = datetime(current_time.year, current_time.month, current_time.day)
    formatted_time = current_time.strftime("%H:%M")

    pipeline = pipelines.get_pipeline_missed_schedule_slots(formatted_time)
    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)

    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    # for pending_schedule in pending_schedules:
    pipeline = pipelines.get_pipeline_missed_orders(start_of_today, current_time)
    missed_orders = await db.order.aggregate(pipeline=pipeline).to_list(None)

    call_action_config = [
        value
        for key, value in config.DB_CACHE["config"].items()
        if "TIME_SLOT_ID" in key
    ]
    slot_start = user_whatsapp_service.get_slots(call_action_config, "start_time")
    slot_end = user_whatsapp_service.get_slots(call_action_config, "end_time")

    if missed_orders:
        for order in missed_orders:
            order = Order(**order)
            order_updated = _update_order_for_next_slot(order, slot_start, slot_end)
            if not order_updated:
                logger.info(f"No next slot available for order {order.id}")
                continue
            await db.order.replace_one(
                {"_id": order.id},
                order.model_dump(exclude_defaults=True, exclude={"id"}, by_alias=True),
            )
            await create_ironman_order_requests(order, order.user_wa_id)  # type: ignore
    else:
        logger.info("No missed orders found")


def _update_order_for_next_slot(order: Order, slot_start: dict, slot_end: dict) -> bool:
    """Update order details for the next available time slot.

    Args:
        order: Order to update
        slot_start: Dictionary of slot start times
        slot_end: Dictionary of slot end times

    Returns:
        bool: True if update successful, False if no next slot available
    """
    order_status = []
    if hasattr(order, "order_status") and order.order_status:
        order_status = list(order.order_status)

    i = 0
    while i < len(order_status):
        if getattr(order_status[i], "status", None) == "PICKUP_PENDING":
            del order_status[i]
            i = i - 1
        i = i + 1

    next_slot = cache.get_next_time_slot(order.time_slot)
    if next_slot is None:
        return False  # comment this if you want handle missing next day too
        next_slot = config.DB_CACHE["ordered_time_slots"][0]["key"] + "T"

    now = datetime.now()
    h, m = user_whatsapp_service.get_time_from_stamp(slot_start[next_slot["key"]])
    he, me = user_whatsapp_service.get_time_from_stamp(slot_end[next_slot["key"]])
    start_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
    end_time = now.replace(hour=he, minute=me, second=0, microsecond=0)
    pickup_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    order.time_slot = next_slot["key"]
    order.updated_on = now
    order.pickup_date_time = PickupDateTime(
        start=start_time, end=end_time, date=pickup_date
    )
    order.service_location_id = None
    order.auto_alloted = None

    return True


async def reset_daily_config():
    logger.info("Started reset_daily_config")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Get daily config reset record
    daily_reset = await db.config.find_one({"key": "daily_config_reset"})

    if (
        not daily_reset
        or daily_reset.get("date").replace(hour=0, minute=0, second=0, microsecond=0)
        != today
    ):
        # Update timeslot volume archive pending flag
        await db.config.update_one(
            {"key": "is_timeslot_volume_archive_pending"},
            {"$set": {"value": True}},
            upsert=True,
        )

        # Update all timeslot configs
        result = await db.config.update_many(
            {
                "key": {
                    "$in": [
                        "TIME_SLOT_ID_1",
                        "TIME_SLOT_ID_2",
                        "TIME_SLOT_ID_3",
                        "TIME_SLOT_ID_4",
                    ]
                }
            },
            {
                "$set": {
                    "is_pending_schedule_pending": True,
                    "is_work_schedule_pending": True,
                    "is_delivery_schedule_pending": True,
                    "is_reassign_pending": True,
                }
            },
        )

        # Finally Update the daily reset record with today's date
        await db.config.update_one(
            {"key": "daily_config_reset"},
            {"$set": {"date": datetime.now()}},
            upsert=True,
        )

        logger.info("Reset %d timeslot configs", result.modified_count)
    else:
        logger.info("Daily config already reset for today")
