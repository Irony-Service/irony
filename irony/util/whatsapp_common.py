import random

from irony.config import config

sample_interactive = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "918328223386",
    "type": "interactive",
    "interactive": {},
}


def get_random_one_from_messages(message_doc):
    return message_doc["message_options"][
        random.randint(0, len(message_doc["message_options"]) - 1)
    ]
