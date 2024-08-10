from datetime import datetime
import json
import random
from fastapi.encoders import jsonable_encoder

import requests

from irony.config import config
from irony.models.contact_details import ContactDetails
from irony.models.order import Order
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.user import User
from irony.config.logger import logger

from . import whatsapp_common

from .message import Message

from irony.db import db


async def handle_message(message_details, contact_details: ContactDetails):
    buttons = config.BUTTONS
    logger.info("message type interactive")
    interaction = message_details["interactive"]
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
            # message_body["interactive"]["body"]["text"] = message_text.replace(
            #     "{greeting}", f"Hey {contact_details['name']} 👋 "
            # )

            last_message_update = {"type": "MAKE_NEW_ORDER"}

        # if quick reply is for clothes count question
        elif str(button_reply_obj["id"]).startswith(config.CLOTHES_COUNT_KEY):
            user: User = await db.user.find_one({"wa_id": contact_details["wa_id"]})

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

            logger.info(order_doc, order_status_doc)

            message_doc = await db.message_config.find_one(
                {"message_key": "new_order_step_2"}
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

    # message_body["to"] = contact_details["wa_id"]

    logger.info("messages endpoint body : {message_body}")
    response = Message(message_body).send_message(contact_details["wa_id"])
    response_data = response.json()

    if last_message_update != None:
        last_message_update["user"] = contact_details["wa_id"]
        if "messages" in response_data and "id" in response_data["messages"][0]:
            last_message_update["last_sent_msg_id"] = response_data["messages"][0]["id"]
        await db.last_message.update_one(
            {"user": contact_details["wa_id"]},
            {"$set": last_message_update},
            upsert=True,
        )

    logger.info("messages response : {response_data}")
