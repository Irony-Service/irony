from typing import Dict, List

from irony.config import config, logger
from irony.db import db
from irony.exception.WhatsappException import WhatsappException
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
    db_cache["ordered_time_slots"] = get_time_slots_ordered_list(configs)

    db_cache["google_maps_link"] = "https://www.google.com/maps/search/?api=1&query="

    return db_cache


def get_time_slots_ordered_list(config_docs: List[Dict]):
    time_slot_docs = [
        config_doc
        for config_doc in config_docs
        if config_doc.get("type", "") == "ironman_schedule"
        and config_doc.get("group", "") == "TIME_SLOT_ID"
    ]
    time_slot_docs.sort(key=lambda slot: slot["start_time"])
    return time_slot_docs


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

def get_title_timeslot(id):
    return config.DB_CACHE["call_to_action_docs"][id["key"]]["value"]


def get_next_time_slot(slot_key):
    time_slot_index = next(
        (
            i
            for i, time_slot_obj in enumerate(config.DB_CACHE["ordered_time_slots"])
            if time_slot_obj["key"] == slot_key
        ),
        None,
    )
    if time_slot_index is None:
        logger.error(
            "Developer concern, for get_next_time_slot, unable to find given slot in db_cache stored time_slots. slot_key %s",
            slot_key,
        )
        raise WhatsappException(config.DEFAULT_ERROR_REPLY_MESSAGE)
    elif time_slot_index == len(config.DB_CACHE["ordered_time_slots"]) - 1:
        return None

    return config.DB_CACHE["ordered_time_slots"][time_slot_index + 1]
