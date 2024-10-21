from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import copy  # Add this import

from irony.config.logger import logger
from irony.config.config import BUTTONS
from irony.db import db
from irony.models.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status import OrderStatusEnum
from irony.models.service_location import (
    DeliveryTypeEnum,
    ServiceLocation,
    ServiceEntry,
)
from irony.models.user import User
from irony.util.message import Message
import irony.util.whatsapp_common as whatsapp_common
import asyncio


# async def find_ironman(user: User, location: UserLocation, order: Order):
#     # create a 2d sphere index for a service location table
#     # find all records within 2km.
#     pipeline = [
#         {
#             "$geoNear": {
#                 "key": "coords",
#                 "near": {"type": "Point", "coordinates": location.location.coordinates},
#                 "distanceField": "distance",
#                 "maxDistance": 2000,
#                 "spherical": True,
#             }
#         },
#         {"$match": {"range": {"$lte": 2000}}},
#         {"$sort": {"distance": 1}},
#         {"$limit": 10},
#     ]

#     nearby_service_locations = await db.service_locations.aggregate(
#         pipeline=pipeline
#     ).to_list(10)

#     if not nearby_service_locations:
#         # send message to user that no ironman found.
#         message_doc = await db.message_config.find_one(
#             {"message_key": "new_order_no_ironman"}
#         )
#         message_body = message_doc["message"]
#         message_text: str = whatsapp_common.get_random_one_from_messages(message_doc)
#         message_body["text"]["body"] = message_text
#         await Message(message_body).send_message(user["wa_id"])
#         raise Exception("No nearby ironman found.")

#     order_requests: List[OrderRequest] = []
#     current_time = datetime.now()
#     nearby_service_locations_dict = {
#         str(service_location["_id"]): service_location
#         for service_location in nearby_service_locations
#     }

#     for index, service_location in enumerate(nearby_service_locations):
#         trigger_time = current_time + timedelta(minutes=index * 15)
#         order_request = OrderRequest(
#             order_id=str(order["_id"]),
#             service_location_id=str(service_location["_id"]),
#             distance=service_location["distance"],
#             trigger_time=trigger_time,
#             is_pending=True,
#             try_count=0,
#         )
#         order_requests.append(order_request)

#     result = await db.order_request.insert_many(
#         [
#             order_request.model_dump(exclude_defaults=True)
#             for order_request in order_requests
#         ]
#     )

#     # Access the inserted record IDs
#     inserted_ids = result.inserted_ids
#     if inserted_ids:
#         inserted_order_requests = await db.order_request.find(
#             {"_id": {"$in": inserted_ids}}
#         ).to_list(length=len(inserted_ids))

#         num_inserted = len(inserted_ids)
#         print(f"Inserted {num_inserted} rows.")
#         tasks = []
#         for order_request in inserted_order_requests:
#             service_location = nearby_service_locations_dict[
#                 order_request["service_location_id"]
#             ]
#             message_doc = await db.message_config.find_one(
#                 {"message_key": "new_order_send_ironman_request"}
#             )
#             message_body = message_doc["message"]
#             message_text: str = whatsapp_common.get_random_one_from_messages(
#                 message_doc
#             )
#             message_text = (
#                 message_text.replace(
#                     "{service_location_name}",
#                     service_location.get("name", "Service Provider"),
#                 )
#                 .replace("{dist}", str(order_request.get("distance", "NA")))
#                 .replace(
#                     "{count}",
#                     BUTTONS.get(order.get("count_range"), {}).get("title", "NA"),
#                 )
#                 .replace("{amount}", order.get("total_price", "NA"))
#             )
#             message_body["interactive"]["body"]["text"] = message_text
#             tasks.append(Message(message_body).send_message(service_location["wa_id"]))
#         await asyncio.gather(*tasks)


async def find_ironman(order: Order, contact_details: ContactDetails):
    location: Location = await db.location.find_one({"_id": order.location_id})
    # create a 2d sphere index for a service location table
    # find all records within 2km.
    pipeline = [
        {
            "$geoNear": {
                "key": "coords",
                "near": {"type": "Point", "coordinates": location.location.coordinates},
                "distanceField": "distance",
                "maxDistance": 2000,
                "spherical": True,
            }
        },
        {
            "$match": {
                "services.service_id": {
                    "$in": [service._id for service in order.services]
                }
            }
        },
        {"$match": {"range": {"$gte": "$distance"}}},
        {
            "$project": {
                "services_dict": {
                    "$arrayToObject": {
                        "$map": {
                            "input": "$services",
                            "as": "service",
                            "in": {
                                "k": "$$service.service_id",  # Key is the activity's `id`
                                "v": "$$service",  # Value is the activity object itself
                            },
                        }
                    }
                },
            }
        },
        {"$sort": {"distance": 1}},
        {"$limit": 10},
    ]

    nearby_service_locations: List[ServiceLocation] = (
        await db.service_locations.aggregate(pipeline=pipeline).to_list(10)
    )

    if not nearby_service_locations:
        # send message to user that no ironman found.
        message_body = whatsapp_common.get_reply_message(
            "new_order_no_ironman", message_type="text"
        )
        await Message(message_body).send_message(contact_details.wa_id)
        raise Exception("No nearby ironman found.")

    # Split nearby_service_locations into a dictionary based on delivery_type
    nearby_service_locations_dict = {
        DeliveryTypeEnum.DELIVERY: [],
        DeliveryTypeEnum.SELF_PICKUP: [],
    }

    for service_location in nearby_service_locations:
        # first check if service completed_count is less than daily_count for that service.
        delivery_type = service_location.get("delivery_type", DeliveryTypeEnum.DELIVERY)
        nearby_service_locations_dict[delivery_type].append(service_location)

    # # Sort each list by distance
    # for delivery_type in nearby_service_locations_dict:
    #     nearby_service_locations_dict[delivery_type].sort(key=lambda x: x["distance"])

    order_requests: List[OrderRequest] = []
    trigger_time = datetime.now()

    self_pickup_service_locations = nearby_service_locations_dict[
        DeliveryTypeEnum.SELF_PICKUP
    ]
    for index, service_location in enumerate(self_pickup_service_locations):
        trigger_time = trigger_time + timedelta(minutes=index * 15)
        order_request = OrderRequest(
            order_id=order["_id"],
            delivery_type=DeliveryTypeEnum.SELF_PICKUP,
            service_location_id=service_location["_id"],
            distance=service_location["distance"],
            trigger_time=trigger_time,
            is_pending=True,
            try_count=0,
        )
        order_requests.append(order_request)

    # delivery type service location's order request will be created here
    delivery_service_locations = nearby_service_locations_dict[
        DeliveryTypeEnum.DELIVERY
    ]

    delivery_service_locations_ids = [
        service_location["_id"] for service_location in delivery_service_locations
    ]
    trigger_time = trigger_time + timedelta(minutes=15)

    order_request = OrderRequest(
        order_id=order["_id"],
        delivery_type=DeliveryTypeEnum.DELIVERY,
        delivery_service_locations_ids=delivery_service_locations_ids,
        trigger_time=trigger_time,
        is_pending=True,
        try_count=0,
    )
    order_requests.append(order_request)

    result = await db.order_request.insert_many(
        [
            order_request.model_dump(exclude_defaults=True)
            for order_request in order_requests
        ]
    )

    logger.info(
        f"Inserted {len(result.inserted_ids)} rows. Into order_request collection. ids : {result.inserted_ids}"
    )


async def send_ironman_request():
    logger.info("started send_ironman_request")
    logger.info("Finding pending orders")
    current_time = datetime.now()
    pending_orders = await db.order_request.find(
        {
            "trigger_time": {"$lt": current_time},
            "is_pending": True,
            "try_count": {"$lt": 3},
        }
    ).to_list(None)
    pending_orders = [OrderRequest(**order_request) for order_request in pending_orders]

    service_locations = await db.service_locations.find(
        {
            "_id": {
                "$in": [
                    order_request.service_location_id
                    for order_request in pending_orders
                ]
            }
        }
    ).to_list(None)
    service_locations = [
        ServiceLocation(**service_location) for service_location in service_locations
    ]

    # Store service locations in a dictionary with _id as key
    service_locations_dict: Dict[str, ServiceLocation] = {
        str(loc._id): loc for loc in service_locations
    }

    # Fetch orders corresponding to the pending order requests
    order_ids = [order_request.order_id for order_request in pending_orders]
    orders = await db.orders.find({"_id": {"$in": order_ids}}).to_list(None)
    orders = [Order(**order) for order in orders]

    # Store orders in a dictionary with _id as key
    orders_dict: Dict[str, Order] = {str(order._id): order for order in orders}

    logger.info(f"Number of pending orders {len(pending_orders)}")
    tasks = []

    message_doc_main = await db.message_config.find_one(
        {"message_key": "new_order_send_ironman_request"}
    )

    order_request_updates = []
    for order_request in pending_orders:
        order = orders_dict[str(order_request.order_id)]
        if order_request.delivery_type == DeliveryTypeEnum.DELIVERY:
            if not order_request.delivery_service_locations_ids:
                logger.info("No ironman found for order", order._id)
                message_body = whatsapp_common.get_reply_message(
                    "new_order_no_ironman", message_type="text"
                )
                # send message to user
                tasks.append(
                    Message(message_body).send_message(
                        db.user.find_one({"_id": order.user_id})
                    )
                )
                continue
            service_entries = await db.service_entry.find(
                {
                    "service_location_id": {
                        "$in": order_request.delivery_service_locations_ids
                    },
                    "service_id": {"$in": [service._id for service in order.services]},
                    "is_active": True,
                }
            ).to_list(None)
            for service_entry in service_entries:
                service_entry = ServiceEntry(**service_entry)
                if (
                    service_entry.assigned_pieces_today + order.total_count
                    < service_entry.daily_piece_limit
                ):
                    # assign the order to service location.
                    service_entry.assigned_pieces_today += order.total_count
                    await db.service_entry.update_one(
                        {"_id": service_entry._id},
                        {
                            "$set": service_entry.model_dump(
                                exclude_unset=True, exclude_defaults=True
                            )
                        },
                    )
                    order_status = await whatsapp_common.update_order_status(
                        order._id, OrderStatusEnum.PICKUP_PENDING
                    )
                    order.service_location_id = service_entry.service_location_id
                    order.status_id = order_status.inserted_id
                    order.updated_on = datetime.now()
                    await db.orders.update_one(
                        {"_id": order._id},
                        {
                            "$set": order.model_dump(
                                exclude_unset=True, exclude_defaults=True
                            )
                        },
                    )
                    # update the order request in the database
                    order_request_updates.append(str(order_request._id))
                    break
        else:
            # Create a copy of message_doc for each iteration
            message_doc = copy.deepcopy(message_doc_main)
            service_location = service_locations_dict[order_request.service_location_id]
            message_body = message_doc["message"]
            message_text: str = whatsapp_common.get_random_one_from_messages(
                message_doc
            )
            message_text = (
                message_text.replace(
                    "{service_location_name}",
                    getattr(service_location, "name", "Service Provider"),
                )
                .replace("{dist}", str(getattr(order_request, "distance", "NA")))
                .replace(
                    "{count}",
                    BUTTONS.get(getattr(order, "count_range", "NA"), {}).get(
                        "title", "NA"
                    ),
                )
                .replace("{amount}", getattr(order, "total_price", "NA"))
            )
            message_body["interactive"]["body"]["text"] = message_text
            tasks.append(Message(message_body).send_message(service_location.wa_id))
            order_request_updates.append(str(order_request._id))
    await asyncio.gather(*tasks)

    await db.order_request.update_many(
        {"_id": {"$in": order_request_updates}},
        {"$set": {"is_pending": False}},
    )
