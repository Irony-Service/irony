import traceback
from typing import List
from fastapi import APIRouter, Request, Response
from irony import config

from irony.routers.util import whatsapp_util
router = APIRouter()

from ..models.user import User
from ..db import get_users, create_user

@router.route("/webhook", methods=["POST", "PUT", "DELETE"], response_model=List[User])  
async def whatsapp(request: Request):
    try: 
        body = await request.body()
        print(f"Smash, POST method(incoming messages and replies) triggered : {body}")
        if(body['entry']):
            entries = body['entry']
            if(whatsapp_util.is_ongoing_or_status_request(entries[0])):
                return Response(status=200)  
            if(len(entries) > 1):
                print("RECEIVED MORE THAN 1 ENTRY")
            else:
                whatsapp_util.handle_entry(entries[0])
    except Exception as e:
        print(f"Error occured in send whatsapp message : {e}")
        traceback.print_exc()
    finally:
        if(entries[0].get('changes', [{}])[0].get('value', {}).get('messages',[{}])[0].get('id', None) != None):
            calls = config['calls']
            calls[entries[0]['changes'][0]['value']['messages'][0]['id']] = None
    return Response(status=200)

@router.get("/webhook", response_model=User)
async def create_user(request: Request):
    print(f"Smash, GET method(verify webhook) triggered : {request.args}")
    if (
    request.args['hub.mode'] == 'subscribe' and
    request.args['hub.verify_token'] == 'tysonitis'):   
        response = Response(request.args['hub.challenge'], status=200)
        response.headers['Content-Type'] = 'text/plain'
        return response