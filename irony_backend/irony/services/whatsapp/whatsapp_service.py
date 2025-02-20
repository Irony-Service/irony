from fastapi import Response

import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config import config
from irony.config.logger import logger
from irony.exception.WhatsappException import WhatsappException
from irony.models.whatsapp.contact_details import ContactDetails
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils


def is_ongoing_or_status_request(message):
    unique_id = None
    try:
        unique_id = message["id"]
    except Exception:
        raise Exception("Unable to read message id from message object.")

    if unique_id in config.CALLS:
        return True

    logger.info("T2")
    config.CALLS.add(unique_id)
    logger.info("T3")
    return False


async def handle_entry(message, contact_details):
    try:
        message_type = message.get("type", None)
        if message_type == "text":
            logger.info("text message received")
            await text_message_service.handle_message(message, contact_details)
        elif message_type == "interactive":
            logger.info("interactive message received")
            await interactive_message_service.handle_message(message, contact_details)
        elif message_type == "location":
            logger.info("location message received")
            await user_whatsapp_service.set_new_order_location(message, contact_details)
    except WhatsappException as e:
        # here we should send error message reply to user.
        logger.error(f"WhatsappException occured in send whatsapp message : {e}")
        await whatsapp_utils.send_error_reply_message(contact_details, e)
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
