from datetime import datetime, timedelta
from typing import List
from irony.config.config import BUTTONS
from irony.db import db
from irony.models.location import UserLocation
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.user import User
from irony.util.message import Message
import irony.util.whatsapp_common as whatsapp_common


async def find_ironman(user: User, location: UserLocation, order: Order):
    # create a 2d sphere index for a service location table
    # find all records within 2km.
    pipeline = [
        {
            "$geoNear": {
                "key": "coords",
                "near": {"type": "Point", "coordinates": location.location.coordinates},
                "distanceField": "distance",
                "maxDistance": 2000,
                "spherical": True,
            }
        },
        {"$match": {"range": {"$lte": 2000}}},
        {"$sort": {"distance": 1}},
        {"$limit": 10},
        # {"$project": {"_id": 0, "name": 1, "location": 1, "distance": 1}},
    ]

    nearby_service_locations = await db.service_locations.aggregate(
        pipeline=pipeline
    ).to_list(10)

    if len(nearby_service_locations) == 0:
        # send message to user that no ironman found.
        message_doc = await db.message_config.find_one(
            {"message_key": "new_order_no_ironman"}
        )
        message_body = message_doc["message"]
        message_text: str = whatsapp_common.get_random_one_from_messages(message_doc)
        message_body["text"]["body"] = message_text
        await Message(message_body).send_message(user["wa_id"])
        raise Exception("No nearby ironman found.")

    order_requests: List[OrderRequest] = []
    current_time = datetime.now()
    nearby_service_locations_dict = {}
    for index, service_location in enumerate(nearby_service_locations):
        nearby_service_locations_dict[str(service_location["_id"])] = service_location
        trigger_time = current_time + timedelta(minutes=index * 15)
        order_request: OrderRequest = OrderRequest(
            order_id=str(order["_id"]),
            service_location_id=str(service_location["_id"]),
            distance=service_location["distance"],
            trigger_time=trigger_time,
            is_pending=True,
            try_count=0,
        )
        order_requests.append(order_request)

    result = await db.order_request.insert_many(
        [
            order_request.model_dump(exclude_defaults=True)
            for order_request in order_requests
        ]
    )

    # Access the inserted record IDs
    inserted_ids = result.inserted_ids
    if len(inserted_ids) > 0:
        inserted_order_requests = await db.order_request.find(
            {"_id": {"$in": inserted_ids}}
        ).to_list(length=len(inserted_ids))

        num_inserted = len(inserted_ids)
        print(f"Inserted {num_inserted} rows.")
        for order_request in inserted_order_requests:
            service_location = nearby_service_locations_dict[
                order_request["service_location_id"]
            ]
            message_doc = await db.message_config.find_one(
                {"message_key": "new_order_send_ironman_request"}
            )
            message_body = message_doc["message"]
            message_text: str = whatsapp_common.get_random_one_from_messages(
                message_doc
            )
            message_text.replace(
                "{service_location_name}",
                service_location.get("name", "Service Provider"),
            )
            message_text.replace("{dist}", str(order_request.get("distance", "NA")))
            message_text.replace(
                "{count}", BUTTONS.get(order.get("count_range"), {}).get("title", "NA")
            )
            message_text.replace("{amount}", order.get("total_price", "NA"))
            message_body["interactive"]["body"]["text"] = message_text
            await Message(message_body).send_message(service_location["wa_id"])
