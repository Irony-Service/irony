import traceback
from typing import List
from fastapi import APIRouter, Query, Request, Response
from .. import config

from irony.routers.util import whatsapp_util

router = APIRouter()

from ..models.user import User
from ..db import get_users, create_user


@router.post("/webhook")
async def whatsapp(request: Request):
    try:
        body = await request.json()
        print(f"Smash, POST method(incoming messages and replies) triggered : {body}")
        if body["entry"]:
            entries = body["entry"]
            if whatsapp_util.is_ongoing_or_status_request(entries[0]):
                return Response(status_code=200)
            if len(entries) > 1:
                print("RECEIVED MORE THAN 1 ENTRY")
            else:
                whatsapp_util.handle_entry(entries[0])
    except Exception as e:
        print(f"Error occured in send whatsapp message : {e}")
        traceback.print_exc()
    finally:
        if (
            entries[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
            .get("id", None)
            != None
        ):
            calls = config.CALLS
            calls[entries[0]["changes"][0]["value"]["messages"][0]["id"]] = None
    return Response(status_code=200)


@router.get("/webhook", response_model=User)
async def create_user(request: Request):
    print(f"Smash, GET method(verify webhook) triggered : {request.query_params}")
    if (
        request.query_params["hub.mode"] == "subscribe"
        and request.query_params["hub.verify_token"] == "tysonitis"
    ):
        response = Response(request.query_params["hub.challenge"], status_code=200)
        response.headers["Content-Type"] = "text/plain"
        return response
