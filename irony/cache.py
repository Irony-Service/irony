from typing import Dict, List
from irony.config import config
from irony.db import db
from irony.models.call_to_action import CallToAction
from irony.models.service import Service


# Example data-fetching function
async def fetch_data_from_db(db_cache: dict):
    # Simulate a database fetch operation
    call_to_action_docs = await db.get_collection("call_to_action").find().to_list()

    call_to_action_list: List[CallToAction] = [
        CallToAction(**doc) for doc in call_to_action_docs
    ]

    db_cache["call_to_action"] = {cta.key: cta.value for cta in call_to_action_list}
    config.BUTTONS = db_cache["call_to_action"]

    # additional data fetching as needed
    service_docs = await db.get_collection("service").find().to_list()

    service_list: List[Service] = [Service(**doc) for doc in service_docs]

    db_cache["service"] = {
        service.call_to_action_key: service for service in service_list
    }

    return db_cache
