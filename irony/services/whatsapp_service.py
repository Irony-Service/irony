from datetime import datetime
from typing import Any, Optional

from fastapi import Response
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.config import config
from irony.util import whatsapp_common
import irony.util.whatsapp_interactive_message as whatsapp_interactive_message
import irony.util.whatsapp_text_message as whatsapp_text_message
from irony.db import db
from irony.models.location import UserLocation
from irony.models.user import User
from irony.models.order import Order
from irony.config.logger import logger


def is_ongoing_or_status_request(message):
    unique_id = None
    try:
        unique_id = message["id"]
    except Exception:
        raise Exception("Unable to read message id from message object.")

    calls = config.CALLS
    if unique_id in calls and bool(calls[unique_id]):
        return True

    calls[unique_id] = True
    return False


async def handle_entry(message, contact_details):
    try:
        message_type = message.get("type", None)
        if message_type == "text":
            logger.info("text message received")
            await whatsapp_text_message.handle_message(message, contact_details)
        elif message_type == "interactive":
            logger.info("interactive message received")
            await whatsapp_interactive_message.handle_message(message, contact_details)
        elif message_type == "location":
            logger.info("location message received")
            await whatsapp_interactive_message.set_new_order_location(
                message, contact_details
            )
    except WhatsappException as e:
        # here we should send error message reply to user.
        logger.error(f"WhatsappException occured in send whatsapp message : {e}")
        await whatsapp_common.send_error_reply_message(contact_details, e)
    return Response(status_code=200)


def get_contact_details(contact) -> ContactDetails:
    if contact is None:
        raise Exception("Contact object is None")
    # raise exception if wa_id is not in contact object.
    if "wa_id" not in contact:
        raise Exception("wa_id not found in contact object")
    contact_details = {
        "name": contact.get("profile", {}).get("name"),
        "wa_id": contact.get("wa_id"),
    }
    return ContactDetails(**contact_details)
