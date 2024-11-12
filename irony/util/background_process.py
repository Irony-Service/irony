from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import copy

from bson import ObjectId  # Add this import

from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.db import db, replace_documents_in_transaction
from irony.models.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status import OrderStatusEnum
from irony.models.service_location import (
    DeliveryTypeEnum,
    ServiceLocation,
    ServiceEntry,
    get_delivery_enum_from_string,
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
    try:

        # create a 2d sphere index for a service location table
        # find all records within 2km.
        pipeline = [
            {
                "$geoNear": {
                    "key": "coords",
                    "near": {
                        "type": "Point",
                        "coordinates": order.location.location.coordinates,
                    },
                    "distanceField": "distance",
                    "maxDistance": 2000,
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
                    "services": {
                        "$elemMatch": {
                            "service_id": {
                                "$in": [service.id for service in order.services]
                            }
                        }
                    },
                }
            },
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
            {"$limit": 10},
        ]

        nearby_service_locations: List[ServiceLocation] = (
            await db.service_locations.aggregate(pipeline=pipeline).to_list(10)
        )
        # return nearby_service_locations
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
            delivery_type = get_delivery_enum_from_string(
                service_location.get("delivery_type")
            )
            nearby_service_locations_dict[delivery_type].append(service_location)

        # # Sort each list by distance
        # for delivery_type in nearby_service_locations_dict:
        #     nearby_service_locations_dict[delivery_type].sort(key=lambda x: x["distance"])

        order_requests: List[OrderRequest] = []
        trigger_time = datetime.now()

        if nearby_service_locations_dict[DeliveryTypeEnum.SELF_PICKUP]:
            self_pickup_service_locations = nearby_service_locations_dict[
                DeliveryTypeEnum.SELF_PICKUP
            ]
            for index, service_location in enumerate(self_pickup_service_locations):
                trigger_time = trigger_time + timedelta(minutes=index * 5)
                order_request = OrderRequest(
                    order_id=order.id,
                    delivery_type=DeliveryTypeEnum.SELF_PICKUP,
                    service_location_id=service_location["_id"],
                    distance=service_location["distance"],
                    trigger_time=trigger_time,
                    is_pending=True,
                    try_count=0,
                )
                order_requests.append(order_request)

        # delivery type service location's order request will be created here
        if nearby_service_locations_dict[DeliveryTypeEnum.DELIVERY]:
            delivery_service_locations = nearby_service_locations_dict[
                DeliveryTypeEnum.DELIVERY
            ]

            delivery_service_locations_ids = [
                service_location["_id"]
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

        result = await db.order_request.insert_many(
            [
                order_request.model_dump(exclude_defaults=True)
                for order_request in order_requests
            ]
        )

        logger.info(
            f"Inserted {len(result.inserted_ids)} rows. Into order_request collection. ids : {result.inserted_ids}"
        )
    except Exception as e:
        logger.error("Exception in find_ironman", exc_info=True)
        pass


async def send_ironman_request():
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
                "localField": "service_location_ids",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match
                "as": "delivery_service_locations",  # output array field for matched documents
            }
        },
        {
            "$unwind": "$service_location"  # flatten if each order has only one service location
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

    ironman_request_msg = whatsapp_common.get_reply_message(
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
                order_request_updates.append(ObjectId(str(order_request.id)))
                no_ironman_message = whatsapp_common.get_reply_message(
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
                service_entries = service_location.services
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

                        order_status = await whatsapp_common.get_new_order_status(
                            order.id, OrderStatusEnum.PICKUP_PENDING
                        )
                        order.service_location_id = service_entry.service_location_id
                        order.order_status.insert(0, order_status)
                        order.updated_on = datetime.now()

                        orders_updates.append(
                            order.model_dump(exclude_defaults=True, by_alias=True)
                        )
                        # update the order request in the database
                        order_request_updates.append(ObjectId(str(order_request.id)))
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
                .replace("{amount}", str(getattr(order, "total_price", "NA")))
            )

            tasks.append(Message(message_doc).send_message(service_location.wa_id))
            order_request_updates.append(ObjectId(str(order_request.id)))

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


# async def send_ironman_request_old():
#     logger.info("started send_ironman_request")
#     logger.info("Finding pending orders")
#     current_time = datetime.now()

#     pipeline = [
#         {
#             "$match": {
#                 "trigger_time": {"$lt": current_time},
#                 "is_pending": True,
#                 "try_count": {"$lt": 3},
#             }
#         },
#         {
#             "$lookup": {
#                 "from": "service_locations",  # the collection to join
#                 "localField": "service_location_id",  # field in orders referencing service_locations._id
#                 "foreignField": "_id",  # field in service_locations to match
#                 "as": "service_location",  # output array field for matched documents
#             }
#         },
#         {
#             "$unwind": "$service_location"  # flatten if each order has only one service location
#         },
#         {
#             "$lookup": {
#                 "from": "order",  # the collection to join
#                 "localField": "order_id",
#                 "foreignField": "_id",
#                 "as": "order",
#             }
#         },
#         {"$unwind": "$order"},  # flatten if each order has only one order
#     ]
#     pending_orders: List[OrderRequest] = await db.order_request.aggregate(
#         pipeline=pipeline
#     ).to_list(None)
#     pending_orders = [OrderRequest(**order_request) for order_request in pending_orders]
#     # pending_orders = await db.order_request.find(
#     #     {
#     #         "trigger_time": {"$lt": current_time},
#     #         "is_pending": True,
#     #         "try_count": {"$lt": 3},
#     #     }
#     # ).to_list(None)
#     # pending_orders_dict: Dict[str, OrderRequest] = {
#     #     str(order_request["order_id"]): OrderRequest(**order_request)
#     #     for order_request in pending_orders
#     # }
#     # pending_orders = [OrderRequest(**order_request) for order_request in pending_orders]

#     # service_location_ids = {
#     #     order_request.service_location_id
#     #     for order_request in pending_orders_dict.values()
#     # }
#     # service_locations = await db.service_locations.find(
#     #     {"_id": {"$in": list(service_location_ids)}}
#     # ).to_list(None)

#     # service_locations_dict: Dict[str, ServiceLocation] = {
#     #     str(service_location["_id"]): ServiceLocation(**service_location)
#     #     for service_location in service_locations
#     # }

#     # # Fetch orders corresponding to the pending order requests
#     # order_ids = list(pending_orders_dict.keys())
#     # orders = await db.orders.find({"_id": {"$in": order_ids}}).to_list(None)

#     # # Store orders in a dictionary with _id as key
#     # orders_dict: Dict[str, Order] = {
#     #     str(order["_id"]): Order(**order) for order in orders
#     # }

#     logger.info(f"Number of pending orders {len(pending_orders)}")
#     tasks = []

#     message_doc_main = await db.message_config.find_one(
#         {"message_key": "new_order_send_ironman_request"}
#     )

#     order_request_updates = []
#     for order_request in pending_orders:
#         # order = orders_dict[str(order_request.order_id)]
#         order = order_request.order
#         if order_request.delivery_type == DeliveryTypeEnum.DELIVERY:
#             # if there are no delivery service locations for this order, send no ironman found as this will execute after all self pickup orders are done.
#             if not order_request.delivery_service_locations_ids:
#                 logger.info("No ironman found for order", order.id)
#                 message_body = whatsapp_common.get_reply_message(
#                     "new_order_no_ironman", message_type="text"
#                 )
#                 # send message to user
#                 tasks.append(
#                     Message(message_body).send_message(
#                         db.user.find_one({"_id": order.user_id})
#                     )
#                 )
#                 continue

#             # Delivery service locations are present.
#             # service_entries = await db.service_entry.find(
#             #     {
#             #         "service_location_id": {
#             #             "$in": order_request.delivery_service_locations_ids
#             #         },
#             #         "service_id": {"$in": [service.id for service in order.services]},
#             #         "is_active": True,
#             #     }
#             # ).to_list(None)

#             service_entries = order_request.service_location.services
#             for i, service_entry in enumerate(service_entries):
#                 service_entry = ServiceEntry(**service_entry)
#                 if (
#                     service_entry.assigned_pieces_today + order.total_count
#                     < service_entry.daily_piece_limit
#                 ):
#                     # assign the order to service location.
#                     service_entry.assigned_pieces_today += order.total_count
#                     await db.service_entry.update_one(
#                         {"_id": service_entry.id},
#                         {
#                             "$set": service_entry.model_dump(
#                                 exclude_unset=True, exclude_defaults=True
#                             )
#                         },
#                     )
#                     order_status = await whatsapp_common.update_order_status(
#                         order.id, OrderStatusEnum.PICKUP_PENDING
#                     )
#                     order.service_location_id = service_entry.service_location_id
#                     order.status_id = order_status.inserted_id
#                     order.updated_on = datetime.now()
#                     await db.orders.update_one(
#                         {"_id": order.id},
#                         {
#                             "$set": order.model_dump(
#                                 exclude_unset=True, exclude_defaults=True
#                             )
#                         },
#                     )
#                     # update the order request in the database
#                     order_request_updates.append(str(order_request.id))
#                     break
#         else:
#             # Create a copy of message_doc for each iteration
#             message_doc = copy.deepcopy(message_doc_main)
#             service_location = service_locations_dict[order_request.service_location_id]
#             message_body = message_doc["message"]
#             message_text: str = whatsapp_common.get_random_one_from_messages(
#                 message_doc
#             )
#             message_text = (
#                 message_text.replace(
#                     "{service_location_name}",
#                     getattr(service_location, "name", "Service Provider"),
#                 )
#                 .replace("{dist}", str(getattr(order_request, "distance", "NA")))
#                 .replace(
#                     "{count}",
#                     BUTTONS.get(getattr(order, "count_range", "NA"), {}).get(
#                         "title", "NA"
#                     ),
#                 )
#                 .replace("{amount}", getattr(order, "total_price", "NA"))
#             )
#             message_body["interactive"]["body"]["text"] = message_text
#             tasks.append(Message(message_body).send_message(service_location.wa_id))
#             order_request_updates.append(str(order_request.id))
#     await asyncio.gather(*tasks)

#     await db.order_request.update_many(
#         {"_id": {"$in": order_request_updates}},
#         {"$set": {"is_pending": False}},
#     )
