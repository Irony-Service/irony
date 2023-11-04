from ... import config
import irony.routers.util.whatsapp_interactive_message as whatsapp_interactive_message, irony.routers.util.whatsapp_text_message as whatsapp_text_message

def is_ongoing_or_status_request(entry):
    unique_id = None
    try:
        unique_id = entry['changes'][0]['value']['messages'][0]['id']
    except Exception:
        try:
            unique_id = entry['changes'][0]['value']['statuses'][0]['id']
            if(unique_id != None and len(unique_id)>0):
                return True
        except:
            raise Exception("Unable to read neither message id nor message status")

    calls = config['calls']
    if(unique_id in calls and bool(calls[unique_id])) :
        return True

    calls[unique_id] = True
    return False

def handle_entry(entry):
    # get contact name.
    changes_obj = entry['changes'][0]
    contact_details = None
    if ('contacts' in changes_obj['value']):
        contact_details = get_contact_details(changes_obj['value']['contacts'][0])
    
    if ('messages' in changes_obj['value']):
        # get user message
        message_details = changes_obj['value']['messages'][0]
        
        if('type' in message_details):
            if(message_details['type'] == "text"):
                whatsapp_text_message.handle_message(message_details, contact_details)
            elif(message_details['type'] == "interactive"):
                # handle interactive message
                whatsapp_interactive_message.handle_message(message_details, contact_details)

def get_contact_details(contact):
    return {'name' : contact['profile']['name'], 'wa_id': contact['wa_id']}