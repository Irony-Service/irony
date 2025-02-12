from datetime import datetime
import random
from typing import Dict

from irony.db import db
from irony.config import config
from irony.config.logger import logger
from irony.exception.WhatsappException import WhatsappException
from irony.models.whatsapp.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.message import MessageConfig, MessageType
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.util.message import Message

sample_interactive = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "918328223386",
    "type": "interactive",
    "interactive": {},
}


def get_random_one_from_messages(message_doc: MessageConfig):
    if message_doc.message_options is None:
        logger.error(
            "Developer concern, No message options for message_doc with _id : %s, message_key: %s",
            message_doc.id,
            message_doc.message_key,
        )
        raise WhatsappException(config.DEFAULT_ERROR_REPLY_MESSAGE)

    return message_doc.message_options[
        random.randint(0, len(message_doc.message_options) - 1)
    ]


def get_contact_details_dict(value) -> dict[str, ContactDetails]:
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
        message_body = get_free_text_message(error.reply_message)
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
        status=status,
        created_on=datetime.now(),
    )

    return await db.order_status.insert_one(
        order_status.model_dump(exclude_defaults=True)
    )


async def get_new_order_status(order_id, status: OrderStatusEnum):
    return OrderStatus(
        order_id=order_id,
        status=status,
        created_on=datetime.now(),
    )


def get_reply_message(message_key, message_type="interactive", message_sub_type=""):
    message_doc: MessageConfig = config.DB_CACHE["message_config"][message_key]
    message_body = message_doc.message
    message_text: str = get_random_one_from_messages(message_doc)
    if message_type == "text":
        message_body["text"]["body"] = message_text
    elif message_type == "interactive":
        message_body["interactive"]["body"]["text"] = message_text
        if message_sub_type == "reply":
            call_to_actions = [
                {
                    "type": "reply",
                    "reply": config.DB_CACHE["call_to_action"][key],
                }
                for key in message_doc.call_to_action
            ]
            message_body["interactive"]["action"]["buttons"] = call_to_actions
        elif message_sub_type == "radio":
            call_to_actions = [
                config.DB_CACHE["call_to_action"][key]
                for key in message_doc.call_to_action
            ]
            message_body["interactive"]["action"]["sections"][0][
                "rows"
            ] = call_to_actions
    # logger.info("message body bitch : ", message_body)
    # logger.info(message_body)
    return message_body


def get_free_text_message(text):
    message_doc: MessageConfig = config.DB_CACHE["message_config"]["free_text"]
    message_body = message_doc.message
    message_body["text"]["body"] = text
    return message_body


async def verify_context_id(contact_details, context):
    if context is None:
        raise WhatsappException(
            "Context is None.", error_code=config.ERROR_CODES["INTERNAL_SERVER_ERROR"]
        )

    last_message = await db.last_message.find_one({"user": contact_details.wa_id})

    if last_message.get("last_sent_msg_id", "POOK") != context:
        logger.info(
            f"Context id is not matching with last message id. Last message : {last_message['last_sent_msg_id']}, User reply context : {context}"
        )

        # TODO uncomment this after before prod
        # raise WhatsappException(
        #     "Context id is not matching with last message id.",
        #     reply_message="Looks like you are replying to some old message. Please reply to the latest message or start a fresh conversation by sending 'Hi'.",
        # )

    return last_message


async def add_user_location(contact_details: ContactDetails, coords):
    location: UserLocation = UserLocation(
        user=contact_details.wa_id,
        location=Location(
            type="Point", coordinates=[coords["latitude"], coords["longitude"]]
        ),
        created_on=datetime.now(),
        last_used=datetime.now(),
    )
    location_doc = await db.location.insert_one(
        location.model_dump(exclude_defaults=True)
    )
    location.id = location_doc.inserted_id
    return location
