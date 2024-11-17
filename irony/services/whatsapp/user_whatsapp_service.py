import asyncio
from datetime import datetime
import json
import random
from typing import Any, List, Optional
from bson import ObjectId
from fastapi import Response
from fastapi.encoders import jsonable_encoder


from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.order import Order
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.service import Service
from irony.models.user import User
from irony.config.logger import logger
from irony.util import background_process, utils

from irony.util import whatsapp_utils

from irony.util.message import Message

from irony.db import db


# Start new order message reply
async def start_new_order(contact_details: ContactDetails):
    last_message_update = None

    message_body = whatsapp_utils.get_reply_message(
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

    await whatsapp_utils.verify_context_id(contact_details, context)

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

    message_body = whatsapp_utils.get_reply_message(
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

    last_message = await whatsapp_utils.verify_context_id(contact_details, context)

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

    message_body = whatsapp_utils.get_reply_message(message_key="ASK_LOCATION")

    last_message_update = {
        "type": config.SERVICE_ID_KEY,
        "order_id": order_doc.id,
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


async def set_new_order_location(message_details, contact_details):
    last_message = await whatsapp_utils.verify_context_id(
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
    message_body = whatsapp_utils.get_reply_message(
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

    last_message = await whatsapp_utils.verify_context_id(contact_details, context)

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

    message_body = whatsapp_utils.get_reply_message(
        message_key="new_order_pending",
        message_sub_type="reply",
    )

    utils.replace_message_keys_with_values(
        message_body,
        {
            # TODO change this to actual chosen date
            "{date}": order.created_on.strftime("%d-%m-%Y"),
            "{time}": config.DB_CACHE["call_to_action"]
            .get(order.time_slot, {})
            .get("title", "N/A"),
        },
    )

    last_message_update = {
        "type": config.TIME_SLOT_ID_KEY,
        "order_id": last_message["order_id"],
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    asyncio.create_task(
        background_process.create_ironman_order_requests(order, contact_details)
    )
