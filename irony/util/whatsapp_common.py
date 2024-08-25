import random
from typing import Dict

from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.models.message import MessageType
from irony.util.message import Message

sample_interactive = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "918328223386",
    "type": "interactive",
    "interactive": {},
}


def get_random_one_from_messages(message_doc):
    return message_doc["message_options"][
        random.randint(0, len(message_doc["message_options"]) - 1)
    ]


def get_contact_details_dict(value) -> ContactDetails:
    contact_list = value.get("contacts", [])
    contact_details_dict: Dict[str, ContactDetails] = {}
    for contact in contact_list:
        whatsapp_id = contact.get("wa_id")
        if contact_details_dict.get(whatsapp_id, None) != None:
            continue

        contact_details = {
            "name": contact.get("profile", {}).get("name"),
            "wa_id": whatsapp_id,
        }
        contact_details_dict[whatsapp_id] = ContactDetails(**contact_details)
    return contact_details_dict


async def send_error_reply_message(
    contact_details: ContactDetails, error: WhatsappException
):
    wa_id = contact_details.wa_id
    if error.reply_message_type == MessageType.TEXT:
        message_body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": wa_id,
            "type": "text",
            "text": {
                "body": error.reply_message,
            },
        }
    elif error.reply_message_type == MessageType.INTERACTIVE:
        message_body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": wa_id,
            "type": "interactive",
            "interactive": error.reply_message,
        }

    return await Message(message_body).send_message(wa_id)


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
