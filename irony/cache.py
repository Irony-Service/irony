from typing import Dict, List
from irony.config import config
from irony.db import db
from irony.models.call_to_action import CallToAction
from irony.models.message import MessageConfig
from irony.models.service import Service


# Example data-fetching function
async def fetch_data_from_db(db_cache: dict):
    # Simulate a database fetch operation
    call_to_action_docs = (
        await db.get_collection("call_to_action").find().sort("order", 1).to_list(None)
    )
    set_call_to_action_cache(call_to_action_docs, db_cache)

    config.BUTTONS = db_cache["call_to_action"]

    # additional data fetching as needed
    service_docs = await db.get_collection("service").find().to_list(None)

    db_cache["services"] = {
        doc["call_to_action_key"]: Service(**doc) for doc in service_docs
    }

    # additional data fetching as needed
    message_configs = await db.get_collection("message_config").find().to_list(None)

    db_cache["message_config"] = {
        message_config["message_key"]: MessageConfig(**message_config)
        for message_config in message_configs
    }

    configs = await db.get_collection("config").find().to_list(None)
    db_cache["config"] = {config["key"]: config for config in configs}

    db_cache["google_maps_link"] = "https://www.google.com/maps/search/?api=1&query="

    return db_cache


def set_call_to_action_cache(call_to_action_docs, db_cache):
    call_to_actions = {}
    call_to_action_groups = {}
    key_to_cta_doc = {}
    for cta in call_to_action_docs:
        call_to_actions[cta["key"]] = cta["value"]
        key_to_cta_doc[cta["key"]] = cta
        if "group" in cta:
            if cta["group"] not in call_to_action_groups:
                call_to_action_groups[cta["group"]] = [cta]
            else:
                call_to_action_groups[cta["group"]].append(cta)

    db_cache["call_to_action"] = call_to_actions
    db_cache["call_to_action_docs"] = key_to_cta_doc
    # db_cache["call_to_action_groups"] = call_to_action_groups


def get_clothes_cta_count(key):
    return config.DB_CACHE["call_to_action_docs"][key]["count"]
