import traceback
from irony.config.config import BUTTONS
from irony.db import db
from irony.config.logger import logger

new_user_greeting_message = """
{greeting} Welcome to Irony, your trusted clothing care partner(Dobbiwala).\nWe're thrilled you've reached out to us.\nWe provide a number of services like Ironing, Washing, Wash and Iron, Dry Clean.\nSit back, relax, and let us take care of your clothing needs with care and efficiency. 🧺✨
"""

new_order_step_1_message = """
We're delighted you're interested in Irony.\nTo make sure we're fully prepared to serve you best, could you please give us an approximate count of the clothing items you plan to have serviced?\nIf it's less than 10 items, we'd appreciate an exact count.\nPlease note that you don't need to specify the services you want at this stage — just the clothing item count will do. The exact cost will be calculated at pickup, and an order will only be created if you're completely satisfied with the price. 🧺✨ \nThank you for choosing Irony, where your convenience comes first! 😊 #IronyLaundry #SimplifyYourLife"
"""

new_order_step_2_message = """
"Great! To schedule your pickup, we'll need your location.\nYou can either share your current location with us on WhatsApp or share a Google Maps address if that's more convenient for you. 📍🗺️ Just let us know, and we'll handle the rest.\nThank you for choosing Irony, where convenience meets quality! 😊 #IronyLaundry #SimplifyYourLife"
"""

new_order_success_message_1 = """
Your Irony pickup is scheduled for {date} at {time}. \n\nOur team will be there to make laundry day hassle-free for you. If there are any changes or if you have specific instructions, feel free to let us know. \nWe look forward to serving you! 🧺✨ #IronyLaundry #SimplifyYourLife
"""

new_order_success_message_2 = """
🚀 Your Irony pickup is all set for [Date] at [Time]! \n\nGet ready for a laundry experience that's as smooth as your freshly cleaned clothes. Any last-minute changes or special instructions? Feel free to share with our delivery executive! We're here to make it easy for you. 🧺✨ #IronyLaundry #SimplifyYourLife
"""
services_message = "We provide a list of services. Please choose one from the options."


async def add_messages():
    try:
        messages = [
            {
                "message_key": "services_message",
                "type": "dynamic",
                "message_options": [services_message],
                "message": {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": None,
                    "type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Choose a service"},
                        "body": {"text": services_message},
                        "footer": {"text": None},
                        "action": {
                            "sections": [
                                {
                                    "title": None,
                                    "rows": [
                                        {
                                            "id": "SERVICE_ID_1",
                                            "title": "Iron",
                                            "description": None,
                                        },
                                        {
                                            "id": "SERVICE_ID_2",
                                            "title": "Wash",
                                            "description": None,
                                        },
                                        {
                                            "id": "SERVICE_ID_3",
                                            "title": "Wash & Iron",
                                            "description": None,
                                        },
                                    ],
                                }
                            ],
                            "button": "Done",
                        },
                    },
                },
            }
            # {
            #     "message_key": "new_user_greeting",
            #     "type": "dynamic",
            #     "message_options": [new_user_greeting_message],
            #     "message": {
            #         "messaging_product": "whatsapp",
            #         "recipient_type": "individual",
            #         "to": None,
            #         "type": "interactive",
            #         "interactive": {
            #             "type": "button",
            #             "header": {"type": "text", "text": "Irony"},
            #             "body": {"text": new_user_greeting_message},
            #             "footer": {"text": "Please select any option from below"},
            #             "action": {
            #                 "buttons": [
            #                     {"type": "reply", "reply": BUTTONS["MAKE_NEW_ORDER"]},
            #                     {"type": "reply", "reply": BUTTONS["PRICES"]},
            #                     {"type": "reply", "reply": BUTTONS["HOW_WE_WORK"]},
            #                 ]
            #             },
            #         },
            #     },
            # },
            # {
            #     "message_key": "new_order_step_1",
            #     "type": "dynamic",
            #     "message_options": [new_order_step_1_message],
            #     "message": {
            #         "messaging_product": "whatsapp",
            #         "recipient_type": "individual",
            #         "to": None,
            #         "type": "interactive",
            #         "interactive": {
            #             "type": "button",
            #             "header": {"type": "text", "text": "Irony"},
            #             "body": {"text": new_order_step_1_message},
            #             "footer": {"text": "Please select any option from below"},
            #             "action": {
            #                 "buttons": [
            #                     {"type": "reply", "reply": BUTTONS["CLOTHES_COUNT_10"]},
            #                     {"type": "reply", "reply": BUTTONS["CLOTHES_COUNT_20"]},
            #                     {
            #                         "type": "reply",
            #                         "reply": BUTTONS["CLOTHES_COUNT_20_PLUS"],
            #                     },
            #                 ]
            #             },
            #         },
            #     },
            # },
            # {
            #     "message_key": "new_order_step_2",
            #     "type": "dynamic",
            #     "message_options": [new_order_step_2_message],
            #     "message": {
            #         "messaging_product": "whatsapp",
            #         "recipient_type": "individual",
            #         "to": None,
            #         "type": "text",
            #         "text": {
            #             "header": {"type": "text", "text": "Irony"},
            #             "body": {"text": new_order_step_2_message},
            #         },
            #     },
            # },
            # {
            #     "message_key": "new_order_success",
            #     "type": "dynamic",
            #     "message_options": [
            #         new_order_success_message_1,
            #         new_order_success_message_2,
            #     ],
            #     "message": {
            #         "messaging_product": "whatsapp",
            #         "recipient_type": "individual",
            #         "to": None,
            #         "type": "interactive",
            #         "interactive": {
            #             "type": "button",
            #             "header": {"type": "text", "text": "Irony"},
            #             "body": {"text": new_order_success_message_1},
            #             "footer": {"text": "Please select any option from below"},
            #             "action": {
            #                 "buttons": [
            #                     {"type": "reply", "reply": BUTTONS["TRACK_ORDER"]},
            #                 ]
            #             },
            #         },
            #     },
            # },
        ]
        messages = await db.message_config.insert_many(messages)
        logger.info(f"Messages inserted : {messages}")
    except Exception as e:
        logger.info(f"Error inserting messages {e}")
        traceback.print_exc()


import asyncio

asyncio.run(add_messages())
