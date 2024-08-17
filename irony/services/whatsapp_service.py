from datetime import datetime
from typing import Any, Optional
from irony.models.contact_details import ContactDetails
from irony.config import config
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


async def handle_entry(entry):
    # get contact name.
    for changes_obj in entry.get("changes", []):
        contact_details: ContactDetails
        if "contacts" in changes_obj.get("value", {}):
            contact_details = get_contact_details(changes_obj["value"]["contacts"][0])

        if "messages" in changes_obj.get("value", {}):
            # get user message
            message_details = changes_obj["value"]["messages"][0]

            if "type" in message_details:
                if message_details["type"] == "text":
                    logger.info("text message received")
                    await whatsapp_text_message.handle_message(
                        message_details, contact_details
                    )
                elif message_details["type"] == "interactive":
                    # handle interactive message
                    logger.info("interactive message received")
                    await whatsapp_interactive_message.handle_message(
                        message_details, contact_details
                    )
                elif message_details["type"] == "location":
                    logger.info("location message received")
                    await whatsapp_interactive_message.handle_location_message(
                        message_details, contact_details
                    )


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
