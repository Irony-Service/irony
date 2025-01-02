import traceback
from fastapi import APIRouter, Request, Response

from irony.util import whatsapp_utils
from ..config import config
from irony.config.logger import logger

from irony.services.whatsapp import whatsapp_service


from ..models.user import User

router = APIRouter()


@router.post("/webhook")
async def whatsapp(request: Request):
    payload = await request.json()
    try:
        logger.info(f"Message Received : {payload}")

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                contacts_details_dict = whatsapp_utils.get_contact_details_dict(value)
                messages = value.get("messages", [])
                for message in messages:
                    try:
                        if whatsapp_service.is_ongoing_or_status_request(message):
                            return Response(status_code=200)
                        else:
                            return await whatsapp_service.handle_entry(
                                message, contacts_details_dict[message["from"]]
                            )
                    except Exception as e:
                        logger.error(f"Error occured in send whatsapp message : {e}")
                        traceback.print_exc()
                    finally:
                        if message.get("id", None) != None:
                            calls = config.CALLS
                            calls[message.get("id")] = None

        # old method.
        # if payload["entry"]:
        #     entries = payload["entry"]
        #     if whatsapp_service.is_ongoing_or_status_request(entries[0]):
        #         return Response(status_code=200)
        #     if len(entries) > 1:
        #         logger.info("RECEIVED MORE THAN 1 ENTRY")
        #     else:
        #         await whatsapp_service.handle_entry(entries[0])
    except Exception as e:
        logger.error(f"Error occured in send whatsapp message : {e}")
        traceback.print_exc()
    return Response(status_code=200)


@router.get("/webhook", response_model=User)
async def verify_webhook(request: Request):
    logger.info(f"GET method(verify webhook) triggered : {request.query_params}")
    if (
        request.query_params["hub.mode"] == "subscribe"
        and request.query_params["hub.verify_token"] == "tysonitis"
    ):
        response = Response(request.query_params["hub.challenge"], status_code=200)
        response.headers["Content-Type"] = "text/plain"
        return response


@router.post("/test")
async def test():
    logger.info("Running erripook")
