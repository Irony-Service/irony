from datetime import datetime
import json
import random
from typing import Any, Optional
from fastapi.encoders import jsonable_encoder

import requests

from irony.config import config
from irony.models.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.order import Order
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.user import User
from irony.config.logger import logger
from irony.util import background_process

from . import whatsapp_common

from .message import Message

from irony.db import db


async def handle_message(message_details, contact_details: ContactDetails):
    buttons = config.BUTTONS
    logger.info("message type interactive")
    interaction = message_details["interactive"]
    context = message_details.get("context", {}).get("id", None)
    message_body = {}
    last_message_update = None
    # Button reply for a quick reply message
    if interaction["type"] == "button_reply":
        logger.info("interaction type button_reply")
        button_reply_obj = interaction[interaction["type"]]

        # raise exception if button is not present in our config.
        if not button_reply_obj.__eq__(buttons[button_reply_obj["id"]]):
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

        # If quick reply is make new order.
        if button_reply_obj["id"] == "MAKE_NEW_ORDER":
            message_doc = await db.message_config.find_one(
                {"message_key": "new_order_step_1"}
            )
            message_body = message_doc["message"]
            message_text: str = whatsapp_common.get_random_one_from_messages(
                message_doc
            )
            message_body["interactive"]["body"]["text"] = message_text

            last_message_update = {"type": "MAKE_NEW_ORDER"}

        # if quick reply is for clothes count question
        elif str(button_reply_obj["id"]).startswith(config.CLOTHES_COUNT_KEY):
            await verify_context_id(contact_details, context)

            user: User = await db.user.find_one({"wa_id": contact_details.wa_id})

            order: Order = Order(
                user_id=user["_id"],
                count_range=button_reply_obj["id"],
                is_active=False,
                created_on=datetime.now(),
            )

            order_doc = await db.order.insert_one(
                order.model_dump(exclude_defaults=True)
            )

            order_status = OrderStatus(
                order_id=order_doc.inserted_id,
                status=OrderStatusEnum.LOCATION_PENDING,
                created_on=datetime.now(),
            )

            order_status_doc = await db.order_status.insert_one(
                order_status.model_dump(exclude_defaults=True)
            )

            # logger.info(order_doc, order_status_doc)

            message_doc = await db.message_config.find_one(
                {"message_key": "services_message"}
            )
            message_body = message_doc["message"]
            message_text: str = whatsapp_common.get_random_one_from_messages(
                message_doc
            )
            message_body["interactive"]["body"]["text"] = message_text

            last_message_update = {
                "type": config.CLOTHES_COUNT_KEY,
                "order_id": order_doc.inserted_id,
            }
        else:
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

    # message_body["to"] = contact_details.wa_id

    logger.info(f"messages endpoint body : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


async def verify_context_id(contact_details, context):
    if context is None:
        raise Exception("Context is None.")

    last_message = await db.last_message.find_one({"user": contact_details.wa_id})

    if last_message["last_sent_msg_id"] != context:
        logger.info(
            f"Context id is not matching with last message id. Last message : {last_message["last_sent_msg_id"]}, User reply context : {context}"
        )
        # raise Exception("Context id is not matching with last message id.")


async def handle_location_message(message_details, contact_details):
    await verify_context_id(
        contact_details, message_details.get("context", {}).get("id", None)
    )
    coords = message_details["location"]
    user: Optional[User] = await db.user.find_one({"wa_id": contact_details.wa_id})
    if user is None:
        raise Exception("User not found.")
    last_message: Any = await db.last_message.find_one({"user": contact_details.wa_id})
    # if last_message["last_sent_msg_id"] != message_details["context"]["id"]:
    #     # return some error kind message because the location reply he has sent might be for other order.
    #     logger.info("Location sent for some older message")

    order: Order = await db.order.find_one({"_id": last_message["order_id"]})
    location: UserLocation = UserLocation(
        user=contact_details.wa_id,
        location=Location(
            type="Point", coordinates=[coords["latitude"], coords["longitude"]]
        ),
        last_used=datetime.now(),
    )
    location_doc = await db.location.insert_one(
        location.model_dump(exclude_defaults=True)
    )

    order["location_id"] = location_doc.inserted_id

    updated_order = await db.order.update_one({"_id": order["_id"]}, {"$set": order})
    if updated_order.modified_count == 0:
        raise Exception("Order not updated with location id.")

    message_doc = await db.message_config.find_one({"message_key": "new_order_pending"})

    message_body = message_doc["message"]
    message_text: str = whatsapp_common.get_random_one_from_messages(message_doc)
    message_body["interactive"]["body"]["text"] = message_text

    last_message_update = {
        "type": config.CLOTHES_COUNT_KEY,
        "order_id": order["_id"],
    }

    logger.info(f"messages endpoint body : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    await background_process.find_ironman(user, location, order)

    logger.info("Location message handled")
    # TODO
    # start background process of searching for nearest ironman to location provided.
    # Send same order to increasing distance wise different ironmans with 10 mins gap if nearest ironman doesn't reply in 5 mins. Take the response of quickest ironman to approve. once a order is approved by an ironman delete the message if possible from other ironman's.
    # Think about what type of application you'll be using. Whether you will use whatsapp messaging only or seperate app for ironman.

    # ironman can specify the location point from where he wants to pickup the order. like a point where 1km around it he wants to accept instead of just from his shop.
