from datetime import datetime
import json
import os
import random
import re

import requests
from app import config
import joblib

from app.models.contact_details import ContactDetails
from app.routers.util.message import Message

from . import whatsapp_common

from ...db import db

# make_prediction = joblib.load('message_classification_function.pkl')
make_prediction = None


def handle_message(message_details, contact_details: ContactDetails):
    print(f"Smash message type text")
    message_body = None
    # user_message = str(message_details["text"]["body"])
    last_message = db.last_messages.find_one({"user": contact_details["wa_id"]})
    print(f"Smash last message: {last_message}")
    # pred = make_prediction([message])
    # print("Smash prediction : ",pred)
    # print("Smash prediction type : ", pred[0])
    # prediction_type = pred[0]
    prediction_type = "start_convo"

    if prediction_type == "start_convo":
        message_body = start_convo(contact_details)
    else:
        # start convo
        message_body = start_convo(contact_details)

    if bool(message_body):
        print(f"Smash, messages endpoint body : {message_body}")
        response = Message(message_body).send_message(contact_details["wa_id"])
        response_data = response.json()
        print(f"Smash, messages response : {response_data}")


def start_convo(contact_details: ContactDetails):
    # Check customer type and return message object
    buttons = config.BUTTONS
    customer_type = whatsapp_common.get_customer_type(contact_details)

    buttons = [
        {"type": "reply", "reply": config.BUTTONS[key]}
        for key in config.BUTTONS.keys()
        if config.CLOTHES_COUNT_KEY in key
    ]
    interactive = {
        "type": "button",
        "header": {"type": "text", "text": "Irony"},  # optional  # end header
        "body": {
            "text": f"{'Hi' if random.randint(1,2) == 1 else 'Hello'} {contact_details['name']}.\nWelcome to Irony. We are a low cost laundry services provider.\n We provide a number of services like Ironing, Washing, Wash and Iron, Dry Clean.\n"
        },
        "footer": {"text": "Please select an option from below"},  # optional
        "action": {"buttons": buttons},  # end action
    }

    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{contact_details.wa_id}",
        "type": "interactive",
        "interactive": interactive,
    }
    return message
