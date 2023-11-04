import random

from irony import config
from .. import screener
from ..db_config import get_db

def handle_fetch_basic_stocks(contact_details):
    db = get_db()['myDatabase']
    buttons = config['BUTTONS']
    fetch_stocks_response = screener.fetch_basic_stocks()
    return internal_fetch_basic_stocks_response(fetch_stocks_response, db, contact_details, buttons)

def handle_failed_basic_stocks_reply(contact_details):
    db = get_db()['myDatabase']
    buttons = config['BUTTONS']
    with current_app.test_client() as client:
        user_last_message = db['last_messages'].find_one({'user' : contact_details['wa_id'], 'type': 'failed_pages'})
        if(user_last_message == None):
            raise Exception("No failed pages found for user")
        response = client.post('/screener/fetchBasicStocksPages', json={'pages': user_last_message['data']})
        return internal_fetch_basic_stocks_response(response.json, db, contact_details, buttons)

def internal_fetch_basic_stocks_response(fetch_stocks_response,db, contact_details, buttons):
    if(fetch_stocks_response["status"] == 'failed'):
        raise Exception(f"Oh no, could not fetch stocks. Something is off. Please come back later. Error message: {fetch_stocks_response['error']}")
    # fetch_stocks_response success
    failed_pages = fetch_stocks_response['data']['failed_pages']
    
    if(len(failed_pages) > 0):
        # send partial success message
        last_messages_collection = db['last_messages']
        last_messages_collection.update_one({"user" : contact_details['wa_id']}, {"$set": {"type" : "failed_pages",  "data" : failed_pages}}, upsert=True)
        body = {
        "type": "button",
        "header": { # optional
            "type": "text",
            "text": "Fetch basic stocks"
        }, # end header
        "body": {
            "text": f"{'Oh no, ' if random.randint(1,2) == 1 else 'Aah, '}.\nFetching is not fully completed. Missed to fetch some pages. {failed_pages}. \nDo you want to trigger them again?"
        },
        "footer": { # optional
            "text": "Please select an option from below"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": buttons['FETCH_FAILED_YES']
                },
                {
                    "type": "reply",
                    "reply": buttons['FETCH_FAILED_NO']
                }
            ] 
        } # end action
        }
    else:
        body = {
        "type": "button",
        "header": { # optional
            "type": "text",
            "text": "Fetch basic stocks"
        }, # end header
        "body": {
            "text": f"{'Yaay! ' if random.randint(1,2) == 1 else 'Hurray! '}.\nCompleted fetching successfully. \nDo you want to generate a report?"
        },
        "footer": { # optional
            "text": "Please select an option from below"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": buttons['GENERATE_YES']
                },
                {
                    "type": "reply",
                    "reply": buttons['GENERATE_NO']
                }
            ] 
        } # end action
        }
        # send full success message
    
    return {"type": "interactive",
            "interactive": body}

sample_interactive = {
      "messaging_product": "whatsapp",
      "recipient_type": "individual",
      "to": "918328223386",
      "type": "interactive",
      "interactive": {}
    }

def handle_generate_report_reply(contact_details):
    db = get_db()['myDatabase']
    latest_searches =  db['latest_searches']
    buttons = config['BUTTONS']
    user_searches_doc = latest_searches.find_one({"user" : contact_details['wa_id']})
    latest_user_searches = None
    interactive = {
        "type" : "button",
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": buttons['SHOW_FIELDS']
                }
            ]
        }
    }
    print(f"Smash searches {user_searches_doc}")
    if(user_searches_doc != None and 'searches' in user_searches_doc and  isinstance(user_searches_doc['searches'], list) and len(user_searches_doc['searches']) > 0):
        latest_user_searches = sorted(user_searches_doc['searches'], key = lambda search: search['last_triggered'], reverse = True)
        message = f"Below are your latest ## report queries, you can select one or provide a new query"
        count = 0
        for search in user_searches_doc['searches']:
            search_message = f"\n {count+1}. {search['query']}"
            if((len(message) + len(search_message) <= 4096) or (count < 9 and (len(message) + len(search_message) <= 4097))):
                count += 1
                message += search_message
            else:
                break
        message = message.replace("##", str(count))
        latest_user_searches = user_searches_doc['searches'][:count]
        user_searches_doc['searches'] = latest_user_searches
        latest_searches.update_one({"_id":user_searches_doc['_id']}, {"$set":{"searches":latest_user_searches}})
        last_messages = db['last_messages']
        last_messages.update_one({'user': contact_details['wa_id']}, {"$set":{"type": "generate_report", "data": latest_user_searches}}, upsert=True)
    else:
        # User has no previous queries. send a enter new query message
        message = f"Looks like you have no previous report queries. Want to know what fields are available?"

    interactive['body'] = {"text": message}
    return {"type": "interactive",
            "interactive": interactive}
    
def handle_show_fields():
    fields_response = screener.fetchFields()
    if(fields_response['status'] == "failed"):
        raise Exception("Unable to fetch fields right now please try again.")
    text = "The are the available fields : "
    text += "\n".join([f"{i + 1}. {field}" for i,field in enumerate(fields_response['data'])]) 
    text += "\nPlease type a query using the fields to generate a report or if you have previous queries send the corresponding number from above." 
    print(f"Smash {text}")
    return {"type": "text", "text": {"body": text}}