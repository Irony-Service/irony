from fastapi import Response


from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails

from irony.config.logger import logger
from irony.services.whatsapp import user_whatsapp_service
from irony.services.whatsapp import ironman_whatsapp_service


from irony.db import db


async def handle_message(message, contact_details: ContactDetails):
    logger.info("message type interactive")
    interaction = message["interactive"]

    # Button reply for a quick reply message
    if interaction["type"] == "button_reply" or interaction["type"] == "list_reply":
        context = message.get("context", {}).get("id", None)
        await handle_button_reply(contact_details, interaction, context)
    return Response(status_code=200)


# Handle button reply for quick reply message
async def handle_button_reply(contact_details: ContactDetails, interaction, context):
    logger.info("Interaction type : button_reply")
    reply = interaction[interaction["type"]]

    # If quick reply is make new order.
    reply_id = reply.get("id", None)
    if reply_id == config.MAKE_NEW_ORDER:
        await user_whatsapp_service.start_new_order(contact_details)
    # if quick reply is for clothes count question
    elif str(reply_id).startswith(config.CLOTHES_COUNT_KEY):
        await user_whatsapp_service.set_new_order_clothes_count(
            contact_details, context, reply
        )
    elif str(reply_id).startswith(config.SERVICE_ID_KEY):
        await user_whatsapp_service.set_new_order_service(
            contact_details, context, reply
        )
    elif str(reply_id).startswith(config.TIME_SLOT_ID_KEY):
        await user_whatsapp_service.set_new_order_time_slot(
            contact_details, context, reply
        )
    elif str(reply_id).startswith(config.IRONMAN_REQUEST):
        await ironman_whatsapp_service.process_ironman_response(
            contact_details, context, reply
        )
        pass
    else:
        logger.error(
            "Button configuration not mathcing. Dev : check config.py button linking"
        )
        raise WhatsappException(
            "Button configuration not mathcing. Dev : check config.py button linking",
            error_code=config.ERROR_CODES["INTERNAL_SERVER_ERROR"],
        )
