from datetime import datetime
import random
from typing import Dict

from irony import db
from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.models.message import MessageType
from irony.models.order_status import OrderStatus, OrderStatusEnum
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


async def update_order_status(order_id, status: OrderStatusEnum):
    order_status = OrderStatus(
        order_id=order_id,
        status=status.value,
        created_on=datetime.now(),
    )

    return await db.order_status.insert_one(
        order_status.model_dump(exclude_defaults=True)
    )


async def get_reply_message(message_key, call_to_action_key=None, message_type=None):
    message_doc = await db.message_config.find_one({"message_key": message_key})
    message_body = message_doc["message"]
    message_text: str = get_random_one_from_messages(message_doc)
    message_body["interactive"]["body"]["text"] = message_text
    if message_type == "reply":
        call_to_actions = [
            {"type": "reply", "reply": value}
            for key, value in config.BUTTONS.items()
            if call_to_action_key in key
        ]
        message_body["interactive"]["action"]["buttons"] = call_to_actions
    elif message_type == "radio":
        call_to_actions = [
            value for key, value in config.BUTTONS.items() if call_to_action_key in key
        ]
        message_body["interactive"]["action"]["sections"]["rows"] = call_to_actions
    return message_body

async def verify_context_id(contact_details, context):
    if context is None:
        raise WhatsappException("Context is None.", error_code=config.ERROR_CODES["INTERNAL_SERVER_ERROR"])

    last_message = await db.last_message.find_one({"user": contact_details.wa_id})

    if last_message["last_sent_msg_id"] != context:
        logger.info(
            f"Context id is not matching with last message id. Last message : {last_message["last_sent_msg_id"]}, User reply context : {context}"
        )
        raise WhatsappException("Context id is not matching with last message id.", reply_message="Looks like you are replying to some old message. Please reply to the latest message or start a fresh conversation by sending 'Hi'.")
    
    return last_message
