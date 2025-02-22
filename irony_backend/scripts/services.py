import traceback
from irony.config.config import BUTTONS
from irony.db import db
from irony.config.logger import logger
from irony.models.location import Location
from irony.models.service import Service
from irony.models.service_location import ServiceLocation, LocationTypeEnum


CLOTHES_COUNT_KEY = "CLOTHES_COUNT"
SERVICE_ID_KEY = "SERVICE_ID"
MAKE_NEW_ORDER = "MAKE_NEW_ORDER"

# BUTTONS: Dict = {
#     f"{CLOTHES_COUNT_KEY}_15_TO_25": {
#         "id": f"{CLOTHES_COUNT_KEY}_15_TO_25",
#         "title": "15-25",
#     },
#     f"{CLOTHES_COUNT_KEY}_25_PLUS": {
#         "id": f"{CLOTHES_COUNT_KEY}_25_PLUS",
#         "title": "25+",
#     },
#     MAKE_NEW_ORDER: {"id": "MAKE_NEW_ORDER", "title": "Make New Order"},
#     "HOW_WE_WORK": {"id": "HOW_WE_WORK", "title": "How we work?"},
#     "TRACK_ORDER": {"id": "TRACK_ORDER", "title": "Track order"},
#     "REFER": {"id": "REFER", "title": "Refer"},
#     "PRICES": {"id": "PRICES", "title": "Prices"},
#     f"{SERVICE_ID_KEY}_1": {
#         "id": f"{SERVICE_ID_KEY}_1",
#         "title": "Iron",
#         "description": None,
#     },
#     f"{SERVICE_ID_KEY}_2": {
#         "id": f"{SERVICE_ID_KEY}_2",
#         "title": "Wash",
#         "description": None,
#     },
#     f"{SERVICE_ID_KEY}_3": {
#         "id": f"{SERVICE_ID_KEY}_3",
#         "title": "Wash & Iron",
#         "description": None,
#     },
# }


async def add_service_locations():
    if "service" not in await db.list_collection_names():
        await db.create_collection("service")
    service = db.get_collection("service")

    indexes = await service.list_indexes().to_list(length=None)
    print(indexes)
    if "service_category_1_service_type_1_service_name_1" not in indexes:
        service.create_index(
            [
                ("service_category", 1),
                ("service_type", 1),
                ("service_name", 1),
            ],  # Fields to index, 1 for ascending order
            unique=True,  # Enforce uniqueness
        )

    if "call_to_action_key" not in indexes:
        service.create_index("call_to_action_key", unique=True)

    services_list = [
        Service(
            service_category="Clothes",
            service_type="Laundry",
            service_name="Wash",
            call_to_action_key=f"{SERVICE_ID_KEY}_2",
        ),
        Service(
            service_category="Clothes",
            service_type="Laundry",
            service_name="Iron",
            call_to_action_key=f"{SERVICE_ID_KEY}_1",
        ),
        Service(
            service_category="Clothes",
            service_type="Laundry",
            service_name="Wash & Iron",
            call_to_action_key=f"{SERVICE_ID_KEY}_3",
        ),
    ]

    result = await service.insert_many(
        [service.model_dump(exclude_defaults=True) for service in services_list]
    )
    print(f"Inserted count: {len(result.inserted_ids)}")

    pass


import asyncio

asyncio.run(add_service_locations())
