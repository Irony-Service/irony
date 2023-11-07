from datetime import datetime
import json
import os
import random
import re

import requests
from irony import config
import joblib

from irony.models.contact_details import ContactDetails
from irony.routers.util.message import Message

from . import whatsapp_common

from ...db import db

# make_prediction = joblib.load('message_classification_function.pkl')
make_prediction = None


def handle_message(message_details, contact_details: ContactDetails):
    print(f"Smash message type text")
    interactive_obj = None
    message_object = None
    message = str(message_details["text"]["body"])
    last_messages = db["last_messages"]
    last_message = last_messages.find_one({"user": contact_details["wa_id"]})
    bearer_token = config.WHATSAPP_CONFIG["bearer_token"]
    print(f"Smash last message: {last_message}")
    # pred = make_prediction([message])
    # print("Smash prediction : ",pred)
    # print("Smash prediction type : ", pred[0])
    # prediction_type = pred[0]
    prediction_type = "start_convo"

    if prediction_type == "start_convo":
        interactive_obj = start_convo(contact_details)
    else:
        # start convo
        print("Smash, d")
        interactive_obj = start_convo(contact_details)

    if bool(interactive_obj) or bool(message_object):
        message_body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": contact_details["wa_id"],
        }
        if bool(interactive_obj):
            message_body = json.dumps(
                {
                    **message_body,
                    "type": "interactive",
                    "interactive": interactive_obj,
                }
            )
        elif bool(message_object):
            message_body = json.dumps({**message_body, **message_object})
        print(f"Smash, messages endpoint body : {message_body}")
        response = Message(message_body).send_message()
        # bearer_token = config.WHATSAPP_CONFIG["bearer_token"]
        # response = requests.post(
        #     "https://graph.facebook.com/v17.0/137217652804256/messages",
        #     headers={
        #         "Content-type": "application/json",
        #         "Authorization": f"Bearer {bearer_token}",
        #     },
        #     data=message_request_body,
        # )
        response_data = response.json()
        print(f"Smash, messages response : {response_data}")


def start_convo(contact_details: ContactDetails):
    # Check customer type and return message object
    buttons = config.BUTTONS
    customer_type = whatsapp_common.get_customer_type(contact_details)
    return {
        "type": "button",
        "header": {"type": "text", "text": "Irony"},  # optional  # end header
        "body": {
            "text": f"{'Hi' if random.randint(1,2) == 1 else 'Hello'} {contact_details['name']}.\nWelcome to Irony. We are a low cost laundry services provider.\n We provide a number of services like Ironing, Washing, Wash and Iron, Dry Clean.\n"
        },
        "footer": {"text": "Please select an option from below"},  # optional
        "action": {
            "buttons": [
                {"type": "reply", "reply": buttons["CLOTHES_COUNT_10"]},
                {"type": "reply", "reply": buttons["CLOTHES_COUNT_20"]},
                {"type": "reply", "reply": buttons["CLOTHES_COUNT_20_PLUS"]},
            ]
        },  # end action
    }
