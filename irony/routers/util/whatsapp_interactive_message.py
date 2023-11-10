import json

import requests

from irony import config
from irony.models.contact_details import ContactDetails

from . import whatsapp_common

from .message import Message

from irony.db import db


def handle_message(message_details, contact_details: ContactDetails):
    buttons = config.BUTTONS
    print(f"Smash message type interactive")
    interaction = message_details["interactive"]
    message_body = {}
    if interaction["type"] == "button_reply":
        print(f"Smash interaction type button_reply")
        button_reply = interaction[interaction["type"]]
        if button_reply != buttons[button_reply["id"]]:
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

        if button_reply["id"] == "MAKE_NEW_ORDER":
            message_body = db.messages.find_one("new_user_greeting")
        elif button_reply["id"] == "FETCH_FAILED_YES":
            message_body = whatsapp_common.handle_failed_basic_stocks_reply(
                contact_details
            )
        else:
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

    base = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": contact_details["wa_id"],
    }
    print(f"Smash message_body : {message_body}")
    message_request_body = json.dumps({**base, **message_body})

    print(f"Smash, messages endpoint body : {message_request_body}")
    response = Message(message_request_body).send_message()
    response_data = response.json()
    print(f"Smash, messages response : {response_data}")
