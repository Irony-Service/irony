import json
import random

import requests

from irony import config
from irony.models.contact_details import ContactDetails

from . import whatsapp_common

from .message import Message

from irony.db import db


async def handle_message(message_details, contact_details: ContactDetails):
    buttons = config.BUTTONS
    print(f"Smash message type interactive")
    interaction = message_details["interactive"]
    message_body = {}
    if interaction["type"] == "button_reply":
        print(f"Smash interaction type button_reply")
        button_reply = interaction[interaction["type"]]
        if not button_reply.__eq__(buttons[button_reply["id"]]):
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

        if button_reply["id"] == "MAKE_NEW_ORDER":
            message_doc = await db.messages.find_one(
                {"message_key": "new_order_step_1"}
            )
            message_body = message_doc["message"]
            message_text: str = message_doc["message_options"][
                random.randint(0, len(message_doc["message_options"]) - 1)
            ]
            # message_body["interactive"]["body"]["text"] = message_text.replace(
            #     "{greeting}", f"Hey {contact_details['name']} 👋 "
            # )

            isUpdated = await db.last_message.update_one(
                {"user": contact_details["wa_id"]},
                {"$set": {"type": "MAKE_NEW_ORDER"}},
                upsert=True,
            )
            print(isUpdated.acknowledged)
        elif button_reply["id"] == "FETCH_FAILED_YES":
            message_body = whatsapp_common.handle_failed_basic_stocks_reply(
                contact_details
            )
        else:
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

    message_body["to"] = contact_details["wa_id"]

    print(f"Smash, messages endpoint body : {message_body}")
    response = Message(message_body).send_message()
    response_data = response.json()
    print(f"Smash, messages response : {response_data}")
