import traceback
from irony.config.config import BUTTONS
from irony.db import db
from irony.config.logger import logger
from irony.models.location import Location
from irony.models.service_location import ServiceLocation, LocationTypeEnum


async def add_service_locations():
    if "service_locations" not in await db.list_collection_names():
        await db.create_collection("service_locations")
    service_location_collection = db.get_collection("service_locations")

    service_location = ServiceLocation(
        name="Asain Laundry",
        coords=Location(
            type="Point", coordinates=[17.44027931797816, 78.33045365256636]
        ),
        range=1200,
        location_type=LocationTypeEnum.OWN,
        total_workforce=5,
        is_active=True,
        rating=5,
    )

    service_location_1 = ServiceLocation(
        name="Srinivasa IT Laundry",
        coords=Location(
            type="Point", coordinates=[17.43327418422371, 78.33408926605767]
        ),
        range=1000,
        location_type=LocationTypeEnum.OUTSOURCE,
        total_workforce=5,
        is_active=True,
        rating=5,
    )

    service_location_2 = ServiceLocation(
        name="Skyview Laundry",
        coords=Location(
            type="Point", coordinates=[17.431038925762667, 78.37564747954913]
        ),
        range=2000,
        location_type=LocationTypeEnum.OUTSOURCE,
        total_workforce=5,
        is_active=True,
        rating=5,
    )

    result = await service_location_collection.insert_many(
        [
            service_location.model_dump(exclude_defaults=True),
            service_location_1.model_dump(exclude_defaults=True),
            service_location_2.model_dump(exclude_defaults=True),
        ]
    )
    print(f"Inserted count: {len(result.inserted_ids)}")

    pass


import asyncio

asyncio.run(add_service_locations())
