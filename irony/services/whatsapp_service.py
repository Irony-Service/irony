from datetime import datetime
from irony.models.contact_details import ContactDetails
from irony.config import config
import irony.util.whatsapp_interactive_message as whatsapp_interactive_message
import irony.util.whatsapp_text_message as whatsapp_text_message
from irony.db import db
from irony.models.location import Location
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
    changes_obj = entry["changes"][0]
    contact_details: ContactDetails = None
    if "contacts" in changes_obj["value"]:
        contact_details = get_contact_details(changes_obj["value"]["contacts"][0])

    if "messages" in changes_obj["value"]:
        # get user message
        message_details = changes_obj["value"]["messages"][0]

        if "type" in message_details:
            if message_details["type"] == "text":
                logger.info("text message received")
                whatsapp_text_message.handle_message(message_details, contact_details)
            elif message_details["type"] == "interactive":
                # handle interactive message
                logger.info("interactive message received")
                await whatsapp_interactive_message.handle_message(
                    message_details, contact_details
                )
            elif message_details["type"] == "location":
                logger.info("location message received")
                coords = message_details["location"]
                user: User = await db.user.find_one({"wa_id": contact_details["wa_id"]})
                last_message = await db.last_message.find_one(
                    {"user": contact_details["wa_id"]}
                )
                if last_message["last_sent_msg_id"] != message_details["context"]["id"]:
                    # return some error kind message because the location reply he has sent might be for other order.
                    logger("Location sent for some older message")

                order: Order = await db.order.find_one(
                    {"_id": last_message["order_id"]}
                )
                location: Location = Location(
                    user=contact_details["wa_id"],
                    location=[(coords["latitude"], coords["longitude"])],
                    last_used=datetime.now(),
                )
                location_doc = await db.location.insert_one(
                    location.model_dump(exclude_defaults=True)
                )

                order["location_id"] = location_doc.inserted_id
                # save order record.


def get_contact_details(contact) -> ContactDetails:
    contact_details = {"name": contact["profile"]["name"], "wa_id": contact["wa_id"]}
    return ContactDetails(**contact_details)
