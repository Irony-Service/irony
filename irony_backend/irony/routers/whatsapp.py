import asyncio
import random
import traceback

from fastapi import APIRouter, Request, Response

from irony.config.logger import logger
from irony.services.whatsapp import whatsapp_service
from irony.util import redis_cache, whatsapp_utils

from ..config import config
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
                        # random_number = random.randint(1, 1000)
                        # logger.info(f"Calls {random_number}: {config.CALLS}")
                        # logger.info(f"Sleeping for 50 ms: {random_number}")
                        # await asyncio.sleep(0.05)
                        # logger.info(f"Completed 50 ms: {random_number}")
                        # logger.info(f"Calls After sleep{random_number}: {config.CALLS}")
                        if not redis_cache.add_message_id(message):
                            logger.info(f"Message under processing: {message}")
                            return {"status": "processing"}, 409

                        logger.info(f"Message Received : {message}")
                        return await whatsapp_service.handle_entry(
                            message, contacts_details_dict[message["from"]]
                        )
                    except Exception as e:
                        logger.error(f"Error occured in send whatsapp message : {e}")
                        traceback.print_exc()
                    # finally:
                    #     if message.get("id", None) != None:
                    #         config.CALLS.remove(message.get("id"))

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
