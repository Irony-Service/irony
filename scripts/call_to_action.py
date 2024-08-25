from typing import List
from irony.config.config import BUTTONS
from irony.db import db
from irony.models.call_to_action import CallToAction

CLOTHES_COUNT_KEY = "CLOTHES_COUNT"
SERVICE_ID_KEY = "SERVICE_ID"
MAKE_NEW_ORDER = "MAKE_NEW_ORDER"

BUTTONS: dict = {
    f"{CLOTHES_COUNT_KEY}_15_TO_25": {
        "id": f"{CLOTHES_COUNT_KEY}_15_TO_25",
        "title": "15-25",
    },
    f"{CLOTHES_COUNT_KEY}_25_PLUS": {
        "id": f"{CLOTHES_COUNT_KEY}_25_PLUS",
        "title": "25+",
    },
    MAKE_NEW_ORDER: {"id": "MAKE_NEW_ORDER", "title": "Make New Order"},
    "HOW_WE_WORK": {"id": "HOW_WE_WORK", "title": "How we work?"},
    "TRACK_ORDER": {"id": "TRACK_ORDER", "title": "Track order"},
    "REFER": {"id": "REFER", "title": "Refer"},
    "PRICES": {"id": "PRICES", "title": "Prices"},
    f"{SERVICE_ID_KEY}_1": {
        "id": f"{SERVICE_ID_KEY}_1",
        "title": "Iron",
        "description": None,
    },
    f"{SERVICE_ID_KEY}_2": {
        "id": f"{SERVICE_ID_KEY}_2",
        "title": "Wash",
        "description": None,
    },
    f"{SERVICE_ID_KEY}_3": {
        "id": f"{SERVICE_ID_KEY}_3",
        "title": "Wash & Iron",
        "description": None,
    },
}


async def add_call_to_action():
    if "call_to_action" not in await db.list_collection_names():
        await db.create_collection("call_to_action")
    call_to_action = db.get_collection("call_to_action")

    indexes = await call_to_action.list_indexes().to_list(length=None)
    if "key" not in indexes:
        call_to_action.create_index("key", unique=True)

    call_to_actions: List[CallToAction] = [
        CallToAction(key=k, value=v) for k, v in BUTTONS.items()
    ]

    result = await call_to_action.insert_many(
        [cta.model_dump(exclude_defaults=True) for cta in call_to_actions]
    )
    print(f"Inserted count: {len(result.inserted_ids)}")

    pass


import asyncio

asyncio.run(add_call_to_action())
