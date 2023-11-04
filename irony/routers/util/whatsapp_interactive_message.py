import json

import requests

from irony import config

from . import whatsapp_common

from .message import Message


def handle_message(message_details, contact_details):
    buttons = config['BUTTONS']
    print(f"Smash message type interactive")
    interaction = message_details['interactive']
    message_body = {}
    if(interaction['type'] == 'button_reply'):
        print(f"Smash interaction type button_reply")
        button_reply = interaction[interaction['type']]
        if(button_reply != buttons[button_reply['id']]):
            raise Exception("Button configuration not mathcing. Dev : check config.py button linking")
        
        if(button_reply['id'] == 'FETCH_BASIC_STOCKS'):
            message_body = whatsapp_common.handle_fetch_basic_stocks(contact_details)
        elif(button_reply['id'] == 'FETCH_FAILED_YES'):
            message_body = whatsapp_common.handle_failed_basic_stocks_reply(contact_details)
        elif(button_reply['id'] == 'GENERATE_YES' or button_reply['id'] == 'GENERATE_REPORT'):
            message_body = whatsapp_common.handle_generate_report_reply(contact_details)
        elif(button_reply['id'] == 'SHOW_FIELDS'):
            # write for show fields
            message_body = whatsapp_common.handle_show_fields()
        else:
            raise Exception("Button configuration not mathcing. Dev : check config.py button linking")
        
    base = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to" : contact_details['wa_id']
    }
    print(f"Smash message_body : {message_body}")
    message_request_body = json.dumps({**base, **message_body})
    
    print(f"Smash, messages endpoint body : {message_request_body}")
    bearer_token = config['WHATSAPP_CONFIG']['bearer_token']
    response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=message_request_body)
    response_data = response.json()
    print(f"Smash, messages response : {response_data}")
    