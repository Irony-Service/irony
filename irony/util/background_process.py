from datetime import datetime, timedelta
from typing import Any, Dict, List
import asyncio
import copy

from bson import ObjectId

from irony.models.pyobjectid import PyObjectId  # Add this import

import pprint
from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models import location
from irony.models.timeslot_volume_plus import TimeslotVolumePlus
from irony.models.whatsapp.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status import OrderStatusEnum
from irony.models.pickup_tIme import PickupDateTime
from irony.services.whatsapp import user_whatsapp_service
from irony.models.service_location import (
    DeliveryTypeEnum,
    ServiceLocation,
    ServiceEntry,
    get_delivery_enum_from_string,
)
from irony.models.whatsapp.contact_details import ContactDetails
from irony.models.timeslot_volume import Quota, TimeslotVolume
from irony.models.user import User
from irony.util import utils
from irony.util.message import Message
import irony.util.whatsapp_utils as whatsapp_utils
import asyncio


async def create_ironman_order_requests(order: Order, wa_id: str):
    try:

        # create a 2d sphere index for a service location table
        # find all records within 2km.

        # services_match_list = [
        #     {"$elemMatch": {"service_id": service.id} for service in order.services}
        # ]

        if not order.location or not order.location.location or not order.services:
            logger.error(
                "Developer concern, Order has required empty value %s but trying to create ironman order requests. order_id : %s",
                {"order.location": order.location, "order.services": order.services},
                order.id,
            )
            raise WhatsappException(config.DEFAULT_ERROR_REPLY_MESSAGE)

        pipeline: List[Dict[str, Any]] = [
            {
                "$geoNear": {
                    "key": "coords",
                    "near": {
                        "type": "Point",
                        "coordinates": order.location.location.coordinates,
                    },
                    "distanceField": "distance",
                    "maxDistance": 10000,
                    "spherical": True,
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$gte": [
                            "$range",
                            "$distance",
                        ]  # Filter where range is greater or equal to distance
                    },
                    "service_ids": {"$all": [service.id for service in order.services]},
                    "time_slots": {"$in": [order.time_slot]},
                }
            },
            {
                "$lookup": {
                    "from": "timeslot_volume",  # the collection to join
                    "localField": "_id",  # field in orders referencing service_locations._id
                    "foreignField": "service_location_id",  # field in service_locations to match
                    "as": "timeslot_volumes",  # output array field for matched documents
                }
            },
            {
                "$group": {
                    "_id": "$delivery_type",  # Group by the "category" field
                    "documents": {
                        "$push": "$$ROOT"
                    },  # Push the entire document into the "documents" array
                }
            },
            # {
            #     "$unwind": "$time_slot_volume"  # flatten if each order has only one service location
            # },
            # {
            #     "$project": {
            #         "distance": 1,
            #         "_id": 1,
            #         # "services_dict": {
            #         #     "$arrayToObject": {
            #         #         "$map": {
            #         #             "input": "$services",
            #         #             "as": "service",
            #         #             "in": {
            #         #                 "k": {
            #         #                     "$toString": "$$service.service_id"
            #         #                 },  # Key is the activity's `id`
            #         #                 "v": "$$service",  # Value is the activity object itself
            #         #             },
            #         #         }
            #         #     }
            #         # },
            #     }
            # },
            {"$sort": {"distance": 1}},
            {"$limit": 25},
        ]

        delivery_type_service_locations_list: List[Dict[str, Any]] = (
            await db.service_locations.aggregate(pipeline=pipeline).to_list(length=None)
        )

        # List[Dict[DeliveryTypeEnum, List[ServiceLocation]]]
        atleast_one_service_location_present = any(
            location_type["documents"]
            for location_type in delivery_type_service_locations_list
        )
        # return nearby_service_locations
        if not atleast_one_service_location_present:
            # send message to user that no ironman found.
            no_ironman_message_body = whatsapp_utils.get_reply_message(
                "new_order_no_ironman", message_type="text"
            )
            await Message(no_ironman_message_body).send_message(wa_id)
            raise Exception("No nearby ironman found.")

        # Split nearby_service_locations into a dictionary based on delivery_type
        # nearby_service_locations_dict = {
        #     DeliveryTypeEnum.DELIVERY: [],
        #     DeliveryTypeEnum.SELF_PICKUP: [],
        # }

        # for service_location in location_type_with_service_locations:
        #     # first check if service completed_count is less than daily_count for that service.
        #     delivery_type = get_delivery_enum_from_string(
        #         service_location.get("delivery_type")
        #     )
        #     nearby_service_locations_dict[delivery_type].append(service_location)

        # Sort each list by distance
        # for delivery_type in nearby_service_locations_dict:
        #     nearby_service_locations_dict[delivery_type].sort(key=lambda x: x["distance"])

        order_requests: List[OrderRequest] = []
        trigger_time = datetime.now()
        # temp_name = ""

        for delivery_type_service_locations in delivery_type_service_locations_list:
            if delivery_type_service_locations["_id"] == DeliveryTypeEnum.SELF_PICKUP:
                self_pickup_service_locations = delivery_type_service_locations[
                    "documents"
                ]
                for index, service_location in enumerate(self_pickup_service_locations):
                    service_location = ServiceLocation(**service_location)
                    if service_location.auto_accept:
                        if await check_limit_and_allot_order(
                            order, service_location, True
                        ):
                            break
                    else:
                        trigger_time = trigger_time + timedelta(minutes=index * 1)
                        order_request = OrderRequest(
                            order_id=order.id,
                            delivery_type=DeliveryTypeEnum.SELF_PICKUP,
                            service_location_id=service_location.id,
                            distance=service_location.distance,
                            trigger_time=trigger_time,
                            is_pending=True,
                            try_count=0,
                        )
                        order_requests.append(order_request)

            # delivery type service location's order request will be created here
            elif delivery_type_service_locations["_id"] == DeliveryTypeEnum.DELIVERY:
                delivery_service_locations = delivery_type_service_locations[
                    "documents"
                ]

                delivery_service_locations_ids = [
                    ServiceLocation(**service_location).id
                    for service_location in delivery_service_locations
                ]

                trigger_time = trigger_time + timedelta(minutes=15)
                order_request = OrderRequest(
                    order_id=order.id,
                    delivery_type=DeliveryTypeEnum.DELIVERY,
                    delivery_service_locations_ids=delivery_service_locations_ids,
                    trigger_time=trigger_time,
                    is_pending=True,
                    try_count=0,
                )
                order_requests.append(order_request)

        if order_requests:
            result = await db.order_request.insert_many(
                [
                    order_request.model_dump(exclude_defaults=True)
                    for order_request in order_requests
                ]
            )

            logger.info(
                f"Inserted {len(result.inserted_ids)} rows. Into order_request collection. ids : {result.inserted_ids}"
            )
        # logger.info(f"Order assigned to ServiceLocation {temp_name}.")
    except Exception as e:
        logger.error("Exception in find_ironman", exc_info=True)
        pass


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

    timeslot_volume: TimeslotVolume | None = next(
        (
            timeslot_volume
            for timeslot_volume in service_location.timeslot_volumes
            if timeslot_volume
            and timeslot_volume.operation_date
            and order.pickup_date_time
            and order.pickup_date_time.start
            and order.pickup_date_time.start.strftime("%Y-%m-%d")
            in str(timeslot_volume.operation_date)
        ),
        None,
    )

    if (
        not timeslot_volume
        or not timeslot_volume.timeslot_distributions
        or not timeslot_volume.services_distribution
    ):
        return False

    timeslot = timeslot_volume.timeslot_distributions[order.time_slot]
    service = timeslot_volume.services_distribution[
        order.services[0].call_to_action_key
    ]

    clothes_count = cache.get_clothes_cta_count(order.count_range)
    if (
        timeslot.limit is not None
        and timeslot.current is not None
        and service.limit is not None
        and service.current is not None
        and timeslot.limit - timeslot.current >= clothes_count
        and service.limit - service.current >= clothes_count
    ):
        timeslot.current += clothes_count
        service.current += clothes_count
        timeslot_volume.current_clothes += clothes_count

        await db.timeslot_volume.replace_one(
            {"_id": timeslot_volume.id},  # Match the document by its _id
            timeslot_volume.model_dump(exclude_defaults=True, exclude={"id"}),
        )

        order_status = await whatsapp_utils.get_new_order_status(
            order.id, OrderStatusEnum.PICKUP_PENDING
        )
        order.service_location_id = service_location.id
        if order.order_status:
            order.order_status.insert(0, order_status)
        order.updated_on = datetime.now()
        if auto_allot:
            order.auto_alloted = True

        await db.order.replace_one(
            {"_id": order.id},
            order.model_dump(exclude_defaults=True, exclude={"id"}, by_alias=True),
        )
        temp_name = service_location.name

        message_body = whatsapp_utils.get_reply_message(
            message_key="new_order_ironman_alloted",
            message_sub_type="text",
        )

        last_message_update = {
            "type": "ORDER_CONFIRMED",
            "order_id": order.id,
            "order_taken": True,
        }

        logger.info(f"Sending message to user : {message_body}")
        await Message(message_body).send_message(order.user_wa_id, last_message_update)
        return True
    return False


async def send_pending_order_requests():
    logger.info("started send_ironman_request")
    logger.info("Finding pending orders")
    current_time = datetime.now()

    pipeline = [
        {
            "$match": {
                "trigger_time": {"$lt": current_time},
                "is_pending": True,
                "try_count": {"$lt": 3},
            }
        },
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "service_location_id",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match
                "as": "service_location",  # output array field for matched documents
            }
        },
        {
            "$unwind": "$service_location"  # flatten if each order has only one service location
        },
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "delivery_service_locations_ids",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match
                "as": "delivery_service_locations",  # output array field for matched documents
            }
        },
        {
            "$lookup": {
                "from": "order",  # the collection to join
                "localField": "order_id",
                "foreignField": "_id",
                "as": "order",
            }
        },
        {"$unwind": "$order"},  # flatten if each order has only one order
    ]
    pending_orders: List[OrderRequest] = await db.order_request.aggregate(
        pipeline=pipeline
    ).to_list(None)

    pending_orders = [OrderRequest(**order_request) for order_request in pending_orders]

    if not pending_orders:
        logger.info("No pending orders found")
        return

    logger.info(f"Number of pending orders {len(pending_orders)}")
    tasks = []

    ironman_request_msg = whatsapp_utils.get_reply_message(
        "new_order_send_ironman_request",
        message_type="interactive",
        message_sub_type="reply",
    )

    order_request_updates = []
    orders_updates = []
    service_locations_updates = []
    for order_request in pending_orders:
        # order = orders_dict[str(order_request.order_id)]
        order = order_request.order
        if order_request.delivery_type == DeliveryTypeEnum.DELIVERY:
            # if there are no delivery service locations for this order, send no ironman found as this will execute after all self pickup orders are done.
            if not order_request.delivery_service_locations_ids:
                logger.info("No ironman found for order", order.id)
                order_request_updates.append(PyObjectId(str(order_request.id)))
                no_ironman_message = whatsapp_utils.get_reply_message(
                    "new_order_no_ironman", message_type="text"
                )
                # send message to user
                tasks.append(
                    Message(no_ironman_message).send_message(
                        db.user.find_one({"_id": order.user_id})
                    )
                )
                continue

            # Delivery service locations are present.
            # service_entries = await db.service_entry.find(
            #     {
            #         "service_location_id": {
            #             "$in": order_request.delivery_service_locations_ids
            #         },
            #         "service_id": {"$in": [service.id for service in order.services]},
            #         "is_active": True,
            #     }
            # ).to_list(None)

            for service_location in order_request.delivery_service_locations:
                service_entries = service_location.service_ids
                for i, service_entry in enumerate(service_entries):
                    order_clothes_count = cache.get_clothes_cta_count(order.count_range)
                    if (
                        order.services[0].id
                        == service_entry.service_id  # Assuming only one service in order
                        and service_entry.assigned_pieces_today + order_clothes_count
                        < service_entry.daily_piece_limit
                    ):
                        # assign the order to service location.
                        service_entries[i].assigned_pieces_today += order_clothes_count
                        service_locations_updates.append(
                            service_location.model_dump(
                                exclude_defaults=True, exclude_unset=True, by_alias=True
                            )
                        )

                        order_status = await whatsapp_utils.get_new_order_status(
                            order.id, OrderStatusEnum.PICKUP_PENDING
                        )
                        order.service_location_id = service_location.id
                        order.order_status.insert(0, order_status)
                        order.updated_on = datetime.now()

                        orders_updates.append(
                            order.model_dump(exclude_defaults=True, by_alias=True)
                        )
                        # update the order request in the database
                        order_request_updates.append(PyObjectId(str(order_request.id)))
                        break
        else:
            # Create a copy of message_doc for each iteration
            service_location = order_request.service_location
            message_doc = copy.deepcopy(ironman_request_msg)

            message_doc["interactive"]["action"]["buttons"] = [
                {
                    **button,
                    "reply": {
                        **button["reply"],
                        "id": str(button["reply"]["id"]) + "#" + str(order_request.id),
                    },
                }
                for button in message_doc["interactive"]["action"]["buttons"]
            ]

            message_doc["interactive"]["body"]["text"] = (
                str(message_doc["interactive"]["body"]["text"])
                .replace(
                    "{service_location_name}",
                    getattr(service_location, "name", "Service Provider"),
                )
                .replace(
                    "{dist}",
                    str(getattr(order_request, "distance", "NA")).split(".")[0]
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
                    .get(order_request.order.time_slot, {})
                    .get("title", "N/A"),
                )
                .replace("{amount}", str(getattr(order, "total_price", "NA")))
            )

            tasks.append(Message(message_doc).send_message(service_location.wa_id))
            order_request_updates.append(PyObjectId(str(order_request.id)))

    # Send all messsages at once
    await asyncio.gather(*tasks)

    if len(orders_updates) > 0:
        await replace_documents_in_transaction("order", orders_updates)

    if len(service_locations_updates) > 0:
        await replace_documents_in_transaction(
            "service_locations", service_locations_updates
        )

    if len(order_request_updates) > 0:
        await db.order_request.update_many(
            {"_id": {"$in": order_request_updates}},
            {"$set": {"is_pending": False}},
        )


async def send_ironman_delivery_schedule():
    logger.info("Started send_ironman_schedule")
    logger.info("Finding pending pickup/drop orders")
    n = config.DB_CACHE["config"]["delivery_schedule_time_gap"]["value"]
    # current_time = datetime.now()
    # start_time = f"{current_time.hour:02d}:{current_time.minute:02d}"
    current_plus_n = datetime.now() + timedelta(minutes=n)
    trigger_time = f"{current_plus_n.hour:02d}:{current_plus_n.minute:02d}"

    # continue here
    # print("08:59">"09:00")
    pipeline = [
        {
            "$match": {
                "start_time": {"$lte": trigger_time},
                "group": "TIME_SLOT_ID",
                "is_delivery_schedule_pending": True,
            }
        }
    ]

    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)
    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    logger.info(f"Number of pending schedules {len(pending_schedules)}")

    collect_message_root = whatsapp_utils.get_reply_message(
        "ironman_collect_order",
        message_type="interactive",
        message_sub_type="reply",
    )

    drop_message_root = whatsapp_utils.get_reply_message(
        "ironman_drop_order", message_type="interactive", message_sub_type="reply"
    )

    for pending_schedule in pending_schedules:
        pipeline = [
            {
                "$match": {
                    "time_slot": pending_schedule["key"],
                    "order_status.0.status": {
                        "$in": [
                            OrderStatusEnum.PICKUP_PENDING,
                            OrderStatusEnum.DELIVERY_PENDING,
                        ]
                    },
                }
            },
            {
                "$lookup": {
                    "from": "user",  # the collection to join
                    "localField": "user_id",  # field in orders referencing service_locations._id
                    "foreignField": "_id",  # field in service_locations to match`
                    "as": "user",  # output array field for matched documents
                }
            },
            {"$unwind": "$user"},
            {
                "$lookup": {
                    "from": "service_locations",  # the collection to join
                    "localField": "service_location_id",  # field in orders referencing service_locations._id`
                    "foreignField": "_id",  # field in service_locations to match
                    "as": "service_location",  # output array field for matched documents
                }
            },
            {"$unwind": "$service_location"},
            {"$sort": {"distance": 1}},
            {
                "$group": {
                    "_id": "$service_location_id",
                    "documents": {
                        "$push": "$$ROOT"
                    },  # Push the entire document into the "documents" list
                }
            },
        ]

        service_location_orders = await db.order.aggregate(pipeline=pipeline).to_list(
            None
        )

        for service_location_order in service_location_orders:
            tasks = []
            orders = service_location_order.documents

            for i, order in enumerate(orders):
                order = Order(**order)

                message = None
                count = None
                link = utils.get_maps_link(order.location)

                if order.order_status[0].status == OrderStatusEnum.PICKUP_PENDING:
                    message = copy.deepcopy(collect_message_root)
                    count = (
                        config.DB_CACHE["call_to_action"]
                        .get(getattr(order, "count_range", "NA"), {})
                        .get("title", "NA")
                    )
                else:
                    message = copy.deepcopy(drop_message_root)
                    count = order.total_count

                message["interactive"]["action"]["buttons"] = [
                    {
                        **button,
                        "reply": {
                            **button["reply"],
                            "id": str(button["reply"]["id"]) + "#" + str(order.id),
                        },
                    }
                    for button in message["interactive"]["action"]["buttons"]
                ]

                message["interactive"]["body"]["text"] = (
                    str(message["interactive"]["body"]["text"])
                    .replace("{sno}", str(i + 1))
                    .replace("{name}", order.user.name)
                    .replace("{count}", str(count))
                    .replace(
                        "{link}",
                        link,
                    )
                    .replace("{phone}", str(order.user.wa_id)[2:])
                    .replace("{amount}", str(getattr(order, "total_price", "NA")))
                )

                # send message to ironman
                tasks.append(
                    Message(message).send_message(order.service_location.wa_id)
                )
            logger.info(
                f"Sending messages to ironman for service location {service_location_order['_id']}"
            )
            await asyncio.gather(*tasks)

        # update schedule status
        await db.config.update_one(
            {"_id": pending_schedule["_id"]},
            {"$set": {"is_delivery_schedule_pending": False}},
        )

    logger.info("Completed send_ironman_schedule")


# New batch to assign unpicked up orders to other ironmans in next schedule asap.
async def assign_missed_pickup_to_other_ironmans(pending_schedule):
    logger.info("Started assign_missed_pickup_to_other_ironmans")


async def send_ironman_work_schedule():
    logger.info("Started send_ironman_schedule")
    logger.info("Finding pending pickup/drop orders")
    n = config.DB_CACHE["config"]["work_schedule_time_gap"]["value"]
    current_minus_n = datetime.now() - timedelta(minutes=n)
    trigger_time = f"{current_minus_n.hour:02d}:{current_minus_n.minute:02d}"

    # continue here
    # print("08:59">"09:00")
    pipeline = [
        {
            "$match": {
                "end_time": {"$lte": trigger_time},
                "is_work_schedule_pending": True,
            }
        }
    ]

    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)
    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    logger.info(f"Number of pending schedules {len(pending_schedules)}")

    for pending_schedule in pending_schedules:
        pipeline = [
            {
                "$match": {
                    "service_location_id": {"$ne": None},
                    "time_slot": pending_schedule["key"],
                    "order_status.0.status": {
                        "$in": [
                            OrderStatusEnum.PICKUP_COMPLETE,
                            OrderStatusEnum.WORK_IN_PROGRESS,
                        ]
                    },
                }
            },
            {
                "$lookup": {
                    "from": "user",  # the collection to join
                    "localField": "user_id",  # field in orders referencing service_locations._id
                    "foreignField": "_id",  # field in service_locations to match`
                    "as": "user",  # output array field for matched documents
                }
            },
            {"$unwind": "$user"},
            {
                "$lookup": {
                    "from": "service_locations",  # the collection to join
                    "localField": "service_location_id",  # field in orders referencing service_locations._id`
                    "foreignField": "_id",  # field in service_locations to match
                    "as": "service_location",  # output array field for matched documents
                }
            },
            {"$unwind": "$service_location"},
            {"$sort": {"distance": 1}},
            {
                "$group": {
                    "_id": "$service_location_id",
                    "documents": {
                        "$push": "$$ROOT"
                    },  # Push the entire document into the "documents" list
                }
            },
        ]

        service_location_orders = await db.order.aggregate(pipeline=pipeline).to_list(
            None
        )

        message_root = whatsapp_utils.get_reply_message(
            "ironman_to_work_order",
            message_type="interactive",
            message_sub_type="reply",
        )

        for service_location_order in service_location_orders:
            tasks = []
            orders = service_location_order.documents

            for i, order in enumerate(orders):
                order = Order(**order)

                message = None
                count = None

                message = copy.deepcopy(message_root)
                count = (
                    config.DB_CACHE["call_to_action"]
                    .get(getattr(order, "count_range", "NA"), {})
                    .get("title", "NA")
                )

                message["interactive"]["action"]["buttons"] = [
                    {
                        **button,
                        "reply": {
                            **button["reply"],
                            "id": str(button["reply"]["id"]) + "#" + str(order.id),
                        },
                    }
                    for button in message["interactive"]["action"]["buttons"]
                ]

                message["interactive"]["body"]["text"] = (
                    str(message["interactive"]["body"]["text"])
                    .replace("{sno}", str(i + 1))
                    .replace("{bag}", "LOL")
                    .replace("{count}", str(count))
                    .replace("{phone}", str(order.user.wa_id)[2:])
                    .replace(
                        "{delivery_date}", str(getattr(order, "delivery_date", "NA"))
                    )
                )

                # send message to ironman
                tasks.append(
                    Message(message).send_message(order.service_location.wa_id)
                )
            logger.info(
                f"Sending messages to ironman for service location {service_location_order['_id']}"
            )
            await asyncio.gather(*tasks)

        # update schedule status
        await db.config.update_one(
            {"_id": pending_schedule["_id"]},
            {"$set": {"is_work_schedule_pending": False}},
        )

    assign_missed_pickup_to_other_ironmans(pending_schedule)
    logger.info("Completed send_ironman_schedule")


async def send_ironman_pending_work_schedule():
    logger.info("Started send_ironman_schedule")
    logger.info("Finding pending pickup/drop orders")
    n = config.DB_CACHE["config"]["pending_schedule_time_gap"]["value"]
    current_minus_n = datetime.now() + timedelta(minutes=n)
    trigger_time = f"{current_minus_n.hour:02d}:{current_minus_n.minute:02d}"

    # continue here
    # print("08:59">"09:00")
    pipeline = [
        {
            "$match": {
                "start_time": {"$lte": trigger_time},
                "is_pending_schedule_pending": True,
            }
        }
    ]

    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)
    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    logger.info(f"Number of pending schedules {len(pending_schedules)}")

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

        pipeline = [
            {
                "$match": {
                    "time_slot": pending_schedule["key"],
                    "order_status.0.status": {
                        "$in": [
                            OrderStatusEnum.PICKUP_COMPLETE,
                            OrderStatusEnum.WORK_IN_PROGRESS,
                        ]
                    },
                    "updated_on": {"$gte": start_datetime, "$lte": end_datetime},
                }
            },
            {
                "$lookup": {
                    "from": "user",  # the collection to join
                    "localField": "user_id",  # field in orders referencing service_locations._id
                    "foreignField": "_id",  # field in service_locations to match`
                    "as": "user",  # output array field for matched documents
                }
            },
            {"$unwind": "$user"},
            {
                "$lookup": {
                    "from": "service_locations",  # the collection to join
                    "localField": "service_location_id",  # field in orders referencing service_locations._id`
                    "foreignField": "_id",  # field in service_locations to match
                    "as": "service_location",  # output array field for matched documents
                }
            },
            {"$unwind": "$service_location"},
            {"$sort": {"distance": 1}},
            {
                "$group": {
                    "_id": "$service_location_id",
                    "documents": {
                        "$push": "$$ROOT"
                    },  # Push the entire document into the "documents" list
                }
            },
        ]

        service_location_orders = await db.order.aggregate(pipeline=pipeline).to_list(
            None
        )

        message_root = whatsapp_utils.get_reply_message(
            "ironman_pending_to_work_order",
            message_type="interactive",
            message_sub_type="reply",
        )

        for service_location_order in service_location_orders:
            tasks = []
            orders = service_location_order.documents

            for i, order in enumerate(orders):
                order = Order(**order)

                message = None
                count = None

                message = copy.deepcopy(message_root)
                count = (
                    config.DB_CACHE["call_to_action"]
                    .get(getattr(order, "count_range", "NA"), {})
                    .get("title", "NA")
                )

                message["interactive"]["action"]["buttons"] = [
                    {
                        **button,
                        "reply": {
                            **button["reply"],
                            "id": str(button["reply"]["id"]) + "#" + str(order.id),
                        },
                    }
                    for button in message["interactive"]["action"]["buttons"]
                ]

                message["interactive"]["body"]["text"] = (
                    str(message["interactive"]["body"]["text"])
                    .replace("{sno}", str(i + 1))
                    .replace("{bag}", "LOL")
                    .replace("{count}", str(count))
                    .replace("{phone}", str(order.user.wa_id)[2:])
                    .replace(
                        "{delivery_date}", str(getattr(order, "delivery_date", "NA"))
                    )
                )

                # send message to ironman
                tasks.append(
                    Message(message).send_message(order.service_location.wa_id)
                )
            logger.info(
                f"Sending messages to ironman for service location {service_location_order['_id']}"
            )
            await asyncio.gather(*tasks)

        # update schedule status
        await db.config.update_one(
            {"_id": pending_schedule["_id"]},
            {"$set": {"is_pending_schedule_pending": False}},
        )

    logger.info("Completed send_ironman_schedule")


async def create_timeslot_volume_record_old():
    source_collection = db["timeslot_volume"]
    archive_collection = db["timeslot_volume_arch"]

    today = datetime.now()
    day_before_yesterday = today - timedelta(days=1)
    start_of_day = datetime(
        day_before_yesterday.year, day_before_yesterday.month, day_before_yesterday.day
    )
    end_of_day = start_of_day + timedelta(days=1)
    tomorrow_date = today + timedelta(days=1)

    pipeline = [
        {"$match": {"operation_date": {"$lt": end_of_day}}}
    ]
    records_to_archive = await source_collection.aggregate(pipeline).to_list(
        length=None
    )

    tomorrow_records = []
    for record in records_to_archive:
        record_copy = copy.deepcopy(record)
        record_copy.pop("_id", None)
        record_copy["operation_date"] = tomorrow_date
        tomorrow_records.append(record_copy)

    if records_to_archive:
        await archive_collection.insert_many(records_to_archive)
        result = await source_collection.delete_many(
            {"operation_date": {"$gte": start_of_day, "$lt": end_of_day}}
        )
        await source_collection.insert_many(tomorrow_records)

        logger.info(
            f"Archived {len(records_to_archive)} records to the archive collection and deleted them from the source collection."
        )
        logger.info(
            f"Deleted {result.deleted_count} records from the source collection."
        )
    else:
        logger.info("No records found for the specified date range.")


async def create_timeslot_volume_record():
    is_timeslot_volumene_archive_pending_key = "is_timeslot_volume_archive_pending"
    archive_status_doc = await db.config.find_one({"key":is_timeslot_volumene_archive_pending_key , "value": True})

    if not archive_status_doc:
        logger.info("Timeslot volume records already archived.")
        return

    source_collection = db["timeslot_volume"]
    archive_collection = db["timeslot_volume_arch"]

    today = datetime.now()
    day_before_yesterday = today - timedelta(days=1)
    start_of_day = datetime(
        day_before_yesterday.year, day_before_yesterday.month, day_before_yesterday.day
    )
    end_of_day = start_of_day + timedelta(days=1)
    tomorrow_date = today + timedelta(days=1)

    # Get all active service locations and store in a dictionary
    # active_service_locations: Dict[str, ServiceLocation] = {}
    # active_service_locations = await db.service_locations.find({"is_active": True}).to_list(None)
    # for service_location in found_active:
    #     active_service_locations[service_location["_id"]] = ServiceLocation(**service_location)

    active_service_locations: List[ServiceLocation] = []
    async for service_location in db.service_locations.find({"is_active": True}):
        active_service_locations.append(ServiceLocation(**service_location))

    pipeline = [
        {"$match": {"operation_date": {"$lt": end_of_day}}},
        # {"$lookup": {"from": "service_locations", "localField": "service_location_id", "foreignField": "_id", "as": "service_location"}},
    ]
    records_found = await source_collection.aggregate(pipeline).to_list(
        length=None
    )
    records_to_archive: List[TimeslotVolume] = [TimeslotVolume(**record) for record in records_found]
    # records_to_archive_timeslot_volume: List[TimeslotVolume] = []

    tomorrow_records : List[TimeslotVolume] = []
    # Create records for tomorrow for all active service locations
    for service_location in active_service_locations:
        new_timeslot_volume = TimeslotVolume()
        new_timeslot_volume.operation_date = tomorrow_date 
        new_timeslot_volume.service_location_id = service_location.id
        new_timeslot_volume.daily_limit = service_location.daily_limit
        new_timeslot_volume.current_clothes = 0
        new_timeslot_volume.timeslot_distributions = service_location.timeslot_distributions
        new_timeslot_volume.services_distribution = service_location.services_distribution
        tomorrow_records.append(new_timeslot_volume)

    if records_to_archive:
        archive_result = await archive_collection.insert_many([records_to_archive_timeslot_volume.model_dump(exclude_unset=True) for records_to_archive_timeslot_volume in records_to_archive])
        result = await source_collection.delete_many(
            {"operation_date": {"$lt": end_of_day}}
        )

        logger.info(
            f"Archived {len(archive_result.inserted_ids)}records to the archive collection and deleted them from the source collection."
        )
        logger.info(
            f"Deleted {result.deleted_count} records from the source collection."
        )

    if tomorrow_records:
        result = await source_collection.insert_many([tomorrow_record.model_dump(exclude_unset=True) for tomorrow_record in tomorrow_records])

        logger.info(
            f"Inserted {len(result.inserted_ids)} records for tomorrow in the source collection."
        )

    else:
        logger.info("No records found for the specified date range.")

    await db.config.update_one({"key": is_timeslot_volumene_archive_pending_key}, {"$set": {"value": False}})
    logger.info("Completed create_timeslot_volume_record and archived the records.")


async def create_order_requests():

    # create_ironman_order_requests(order, contact_details)
    current_time = datetime.now()
    pipeline = [
        {
            "$match": {
                "trigger_order_request_at": {"$lte": current_time},
                "trigger_order_request_pending": True,
            }
        },
    ]

    pending_orders = await db.order.aggregate(pipeline=pipeline).to_list(None)
    if not pending_orders:
        logger.info("No pending orders to create order requests")
        return

    logger.info(f"Number of pending orders {len(pending_orders)}")
    tasks = []
    order_ids = []
    for i in pending_orders:
        order = Order(**i)
        order_ids.append(order.id)
        tasks.append(create_ironman_order_requests(order, order.user_wa_id))

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

    pipeline = [
        {"$match": {"end_time": {"$eq": formatted_time}, "group": "TIME_SLOT_ID"}}
    ]
    pending_schedules = await db.config.aggregate(pipeline=pipeline).to_list(None)

    if not pending_schedules:
        logger.info("No pending schedules found")
        return

    # for pending_schedule in pending_schedules:
    pipeline = [
        {
            "$match": {
                "order_status.0.status": {
                    "$in": [
                        OrderStatusEnum.PICKUP_PENDING,
                    ]
                },
                "pickup_date_time.end": {"$gte": start_of_today, "$lte": current_time},
            }
        },
    ]
    missed_orders = await db.order.aggregate(pipeline=pipeline).to_list(None)

    call_action_config = [
        value
        for key, value in config.DB_CACHE["config"].items()
        if "TIME_SLOT_ID" in key
    ]
    slot_start = user_whatsapp_service.get_slots(call_action_config, "start_time")
    slot_end = user_whatsapp_service.get_slots(call_action_config, "end_time")

    if missed_orders:
        for index, order in enumerate(missed_orders):
            order = Order(**order)
            order_status = order.order_status
            i = 0
            while True:
                if i == len(order_status):
                    break
                if (
                    order_status.__getitem__(i).status == "PICKUP_PENDING"
                ):  # or order_status[i]["status"]  =="FINDING_IRONMAN":
                    del order_status[i]
                    i = i - 1
                i = i + 1

            next_slot = cache.get_next_time_slot(order.time_slot)
            if None == next_slot:
                break  # comment this if you want handle missing next day too
                next_slot = config.DB_CACHE["ordered_time_slots"][0]["key"] + "T"

            l = len(next_slot["key"])
            now = datetime.now()
            h, m = user_whatsapp_service.get_time_from_stamp(
                slot_start[next_slot["key"]]
            )
            he, me = user_whatsapp_service.get_time_from_stamp(
                slot_end[next_slot["key"]]
            )
            start_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            end_time = now.replace(hour=he, minute=me, second=0, microsecond=0)

            order.time_slot = next_slot["key"]
            order.updated_on = now
            order.pickup_date_time = PickupDateTime(start=start_time, end=end_time)
            await db.order.update_one(
                {"_id": order.id},
                {
                    "$set": {
                        **order.model_dump(
                            exclude_defaults=True, exclude={"id"}, by_alias=True
                        ),
                        "service_location_id": None,
                        "auto_alloted": None,
                    }
                },
            )
            await create_ironman_order_requests(order, order.user_wa_id)
    else:
        logger.info("No missed orders found")


async def reset_daily_config():
    logger.info("Started reset_daily_config")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Get daily config reset record
    daily_reset = await db.config.find_one({"key": "daily_config_reset"})

    if not daily_reset or daily_reset.get("date").replace(hour=0, minute=0, second=0, microsecond=0) != today:
        # Update the daily reset record with today's date
        await db.config.update_one(
            {"key": "daily_config_reset"},
            {"$set": {"date": datetime.now()}},
            upsert=True
        )
        
        # Update timeslot volume archive pending flag
        await db.config.update_one(
            {"key": "is_timeslot_volume_archive_pending"},
            {"$set": {"value": True}},
            upsert=True
        )

        # Update all timeslot configs 
        result = await db.config.update_many(
            {"key": {"$in": ["TIME_SLOT_ID_1", "TIME_SLOT_ID_2", "TIME_SLOT_ID_3", "TIME_SLOT_ID_4"]}},
            {"$set": {"is_pending_schedule_pending": True, "is_work_schedule_pending": True, "is_delivery_schedule_pending": True, "is_reassign_pending": True}}
        )

        logger.info(f"Reset {result.modified_count} timeslot configs")
    else:
        logger.info("Daily config already reset for today")