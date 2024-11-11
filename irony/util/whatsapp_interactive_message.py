import asyncio
from datetime import datetime
import json
import random
from typing import Any, List, Optional
from bson import ObjectId
from fastapi import Response
from fastapi.encoders import jsonable_encoder

import requests

from irony import cache
from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.message import MessageType, ReplyMessage
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.service import Service
from irony.models.user import User
from irony.config.logger import logger
from irony.util import background_process, utils

from . import whatsapp_common

from .message import Message

from irony.db import db


async def handle_message(message, contact_details: ContactDetails):
    logger.info("message type interactive")
    interaction = message["interactive"]

    # Button reply for a quick reply message
    if interaction["type"] == "button_reply" or interaction["type"] == "list_reply":
        context = message.get("context", {}).get("id", None)
        await handle_button_reply(contact_details, interaction, context)
    return Response(status_code=200)


# Handle button reply for quick reply message
async def handle_button_reply(contact_details: ContactDetails, interaction, context):
    logger.info("Interaction type : button_reply")
    reply = interaction[interaction["type"]]

    # If quick reply is make new order.
    reply_id = reply.get("id", None)
    if reply_id == config.MAKE_NEW_ORDER:
        await start_new_order(contact_details)
    # if quick reply is for clothes count question
    elif str(reply_id).startswith(config.CLOTHES_COUNT_KEY):
        await set_new_order_clothes_count(contact_details, context, reply)
    elif str(reply_id).startswith(config.SERVICE_ID_KEY):
        await set_new_order_service(contact_details, context, reply)
    elif str(reply_id).startswith(config.TIME_SLOT_ID_KEY):
        await set_new_order_time_slot(contact_details, context, reply)
    elif str(reply_id).startswith(config.IRONMAN_REQUEST):
        await process_ironman_response(contact_details, context, reply)
        pass
    else:
        logger.error(
            "Button configuration not mathcing. Dev : check config.py button linking"
        )
        raise WhatsappException(
            "Button configuration not mathcing. Dev : check config.py button linking",
            error_code=config.ERROR_CODES["INTERNAL_SERVER_ERROR"],
        )


# Start new order message reply
async def start_new_order(contact_details: ContactDetails):
    last_message_update = None

    message_body = whatsapp_common.get_reply_message(
        message_key="new_order_step_1",
        message_sub_type="reply",
    )

    last_message_update = {"type": config.MAKE_NEW_ORDER}

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    # BUG Continue here
    user = await db.user.find_one({"_id": contact_details.wa_id})
    if not user:
        new_user = User(
            wa_id=contact_details.wa_id,
            name=contact_details.name,
            created_on=datetime.now(),
        )
        new_user_json_dump = new_user.model_dump_json()
        logger.info(f"Creating new user : {new_user_json_dump}")
        await db.user.insert_one({new_user.model_dump(exclude_defaults=True)})
        logger.info(f"Created new user : {new_user_json_dump}")


# Set new order clothes count message reply
async def set_new_order_clothes_count(
    contact_details: ContactDetails, context, button_reply_obj
):
    message_body = {}
    last_message_update = None

    await whatsapp_common.verify_context_id(contact_details, context)

    user: User = await db.user.find_one({"wa_id": contact_details.wa_id})

    order_status = OrderStatus(
        status=OrderStatusEnum.SERVICE_PENDING,
        created_on=datetime.now(),
    )

    order: Order = Order(
        user_id=user["_id"],
        count_range=button_reply_obj["id"],
        is_active=False,
        order_status=[order_status],
        created_on=datetime.now(),
    )

    order_doc = await db.order.insert_one(order.model_dump(exclude_defaults=True))
    # logger.info(order_doc, order_status_doc)

    message_body = whatsapp_common.get_reply_message(
        message_key="services_message",
        message_sub_type="radio",
    )

    last_message_update = {
        "type": config.CLOTHES_COUNT_KEY,
        "order_id": order_doc.inserted_id,
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


# Set new order service message reply
async def set_new_order_service(
    contact_details: ContactDetails, context, list_reply_obj
):
    message_body = {}
    last_message_update = None

    last_message = await whatsapp_common.verify_context_id(contact_details, context)

    # user: User = await db.user.find_one({"wa_id": contact_details.wa_id})

    selected_service: Service = config.DB_CACHE["services"][list_reply_obj["id"]]

    order_status = OrderStatus(
        status=OrderStatusEnum.LOCATION_PENDING,
        created_on=datetime.now(),
    )

    order_doc: Order = await db.order.find_one_and_update(
        {"_id": last_message["order_id"]},
        {
            "$set": {
                "services": [
                    selected_service.model_dump(exclude_defaults=True, by_alias=True)
                ]
            },
            "$push": {
                "order_status": {
                    "$each": [order_status.model_dump(exclude={"_id", "order_id"})],
                    "$position": 0,
                }
            },
        },
        return_document=True,
    )
    order_doc = Order(**order_doc)

    message_body = whatsapp_common.get_reply_message(message_key="ASK_LOCATION")

    last_message_update = {
        "type": config.SERVICE_ID_KEY,
        "order_id": order_doc.id,
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


async def set_new_order_location(message_details, contact_details):
    last_message = await whatsapp_common.verify_context_id(
        contact_details, message_details.get("context", {}).get("id", None)
    )
    coords = message_details["location"]

    # last_message: Any = await db.last_message.find_one({"user": contact_details.wa_id})
    # if last_message["last_sent_msg_id"] != message_details["context"]["id"]:
    #     # return some error kind message because the location reply he has sent might be for other order.
    #     logger.info("Location sent for some older message")

    order: Order = await db.order.find_one({"_id": last_message["order_id"]})
    order = Order(**order)
    location: UserLocation = UserLocation(
        user=contact_details.wa_id,
        location=Location(
            type="Point", coordinates=[coords["latitude"], coords["longitude"]]
        ),
        created_on=datetime.now(),
        last_used=datetime.now(),
    )
    location_doc = await db.location.insert_one(
        location.model_dump(exclude_defaults=True)
    )
    location.id = location_doc.inserted_id
    order.location = location

    order_status = OrderStatus(
        status=OrderStatusEnum.TIME_SLOT_PENDING, created_on=datetime.now()
    )

    order.order_status.insert(0, order_status)

    updated_order = await db.order.replace_one(
        {"_id": order.id},
        order.model_dump(exclude_defaults=True, exclude={"id"}, by_alias=True),
    )
    if updated_order.modified_count == 0:
        # TODO : send location interactive message again.
        raise WhatsappException(
            message="Unable to update location for your order.",
            reply_message="Unable to update location for your order. Please try again.",
        )

    # TODO : send time slot message to user.
    # TODO : add time slot action options to call_to_action
    message_body = whatsapp_common.get_reply_message(
        message_key="time_slots_message",
        message_sub_type="radio",
    )

    last_message_update = {
        "type": config.LOCATION,
        "order_id": last_message["order_id"],
    }

    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    # message_doc = await db.message_config.find_one({"message_key": "new_order_pending"})

    # message_body = message_doc["message"]
    # message_text: str = whatsapp_common.get_random_one_from_messages(message_doc)
    # message_body["interactive"]["body"]["text"] = message_text

    # last_message_update = {
    #     "type": config.CLOTHES_COUNT_KEY,
    #     "order_id": order["_id"],
    # }

    # logger.info(f"Sending message to user : {message_body}")
    # await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    # await background_process.find_ironman(user, location, order)

    logger.info("Location message handled")
    # TODO
    # start background process of searching for nearest ironman to location provided.
    # Send same order to increasing distance wise different ironmans with 10 mins gap if nearest ironman doesn't reply in 5 mins. Take the response of quickest ironman to approve. once a order is approved by an ironman delete the message if possible from other ironman's.
    # Think about what type of application you'll be using. Whether you will use whatsapp messaging only or seperate app for ironman.

    # ironman can specify the location point from where he wants to pickup the order. like a point where 1km around it he wants to accept instead of just from his shop.


# Set new order time slot message reply
async def set_new_order_time_slot(
    contact_details: ContactDetails, context, button_reply_obj
):
    message_body = {}
    last_message_update = None

    last_message = await whatsapp_common.verify_context_id(contact_details, context)

    # # user: User = await db.user.find_one({"wa_id": contact_details.wa_id})
    # order_doc: Order = await db.order.find_one({"_id": last_message["order_id"]})
    # order = Order(**order_doc)

    # await background_process.find_ironman(order, contact_details)
    # return

    order_status = OrderStatus(
        status=OrderStatusEnum.FINDING_IRONMAN, created_on=datetime.now()
    )
    order_doc: Order = await db.order.find_one_and_update(
        {"_id": last_message["order_id"]},
        {
            "$set": {"time_slot": button_reply_obj["id"]},
            "$push": {
                "order_status": {
                    "$each": [order_status.model_dump(exclude={"_id", "order_id"})],
                    "$position": 0,
                }
            },
        },
        return_document=True,
    )
    order = Order(**order_doc)

    message_body = whatsapp_common.get_reply_message(
        message_key="new_order_pending",
        message_sub_type="reply",
    )

    last_message_update = {
        "type": config.TIME_SLOT_ID_KEY,
        "order_id": last_message["order_id"],
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    asyncio.create_task(background_process.find_ironman(order, contact_details))


async def process_ironman_response(contact_details: ContactDetails, context, reply):
    # Implement the logic for processing ironman response here
    logger.info("Processing ironman response")
    # Example implementation
    if reply.get("id").startswith(config.IRONMAN_REQUEST + "_ACCEPT"):
        await handle_ironman_accept(contact_details, reply.get("id"))
    elif reply.get("id").startswith(config.IRONMAN_REQUEST + "_REJECT"):
        # we can leave it or trigger the next request to other ironman
        await handle_ironman_reject(contact_details, context)
    else:
        logger.error("Unknown ironman response")
        raise WhatsappException(
            "Unknown ironman response",
            error_code=config.ERROR_CODES["INTERNAL_SERVER_ERROR"],
        )


async def handle_ironman_accept(contact_details: ContactDetails, reply_id):
    order_request_id = reply_id.split("#")[-1]

    pipeline = [
        {"$match": {"_id": ObjectId(order_request_id)}},
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
                "from": "order",  # the collection to join
                "localField": "order_id",
                "foreignField": "_id",
                "as": "order",
            }
        },
        {"$unwind": "$order"},
    ]

    order_request_list: List[OrderRequest] = await db.order_request.aggregate(
        pipeline=pipeline
    ).to_list(length=1)
    order_request: OrderRequest = OrderRequest(**order_request_list[0])
    order = order_request.order
    if order.order_status[0].status == OrderStatusEnum.PICKUP_PENDING:
        # Order already accepted by another ironman : send ironman message that order is already accepted.
        logger.info(f"Order:{order.id} already accepted by another ironman")
        return

    # Implement the logic for handling ironman accept response
    service_entries = order_request.service_location.services
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

            # check if service_location is updating as service_entries is fetchec from order_request.service_location. python reference issue.
            await db.service_location.replace_one(
                {"_id": order_request.service_location_id},
                order_request.service_location.model_dump(
                    exclude_defaults=True, exclude_unset=True, by_alias=True
                ),
            )

            order_status = await whatsapp_common.get_new_order_status(
                order.id, OrderStatusEnum.PICKUP_PENDING
            )
            order.service_location_id = service_entry.service_location_id
            order.order_status.insert(0, order_status)
            order.updated_on = datetime.now()

            # update the order in the database
            await db.order.replace_one(
                {"_id": order.id},
                order.model_dump(exclude_defaults=True, by_alias=True),
            )

            logger.info(
                f"Order:{order.id} accepted by service_location: {order_request.service_location_id} ,ironman:{contact_details.wa_id}"
            )

            # Send message to user that ironman accepted the order.
            user_ironman_alloted_msg = whatsapp_common.get_reply_message(
                message_key="new_order_ironman_alloted",
                message_sub_type="reply",
            )

            user_ironman_alloted_msg["interactive"]["body"]["text"] = (
                utils.replace_keys_with_values(
                    user_ironman_alloted_msg["interactive"]["body"]["text"],
                    {
                        "{service_location_name}": str(
                            getattr(
                                order_request.service_location,
                                "name",
                                "Our Service Provider",
                            )
                        ),
                        "{time}": str(
                            getattr(
                                order_request.order,
                                "time_slot",
                                "N/A",
                            )
                        ),
                    },
                )
            )

            await Message(user_ironman_alloted_msg).send_message(contact_details.wa_id)

            # Send message to ironman that order is assigened to him.
            ironman_order_alloted_message = whatsapp_common.get_reply_message(
                message_key="ironman_order_alloted", message_type="text"
            )

            ironman_order_alloted_message["text"]["body"] = (
                utils.replace_keys_with_values(
                    ironman_order_alloted_message["text"]["body"],
                    {
                        "{time}": config.DB_CACHE["call_to_action"]
                        .get(
                            order_request.order.time_slot
                            # str(
                            #     getattr(
                            #         order_request.order,
                            #         "time_slot",
                            #         "N/A",
                            #     )
                            # )
                        )
                        .get("title", "N/A"),
                    },
                )
            )

            await Message(ironman_order_alloted_message).send_message(
                contact_details.wa_id
            )

    logger.info("Ironman accepted completed")


async def handle_ironman_reject(contact_details: ContactDetails, context):
    # Implement the logic for handling ironman reject response
    logger.info("Ironman rejected the request")
