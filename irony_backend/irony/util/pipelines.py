from typing import List

from fastapi.background import P

from irony.models.order_status_enum import OrderStatusEnum
from irony.models.pyobjectid import PyObjectId


def get_pipeline(func_name: str, *args):
    func_map = {
        "orders_group_by_status_and_date_and_time_slot_for_agent_locations": get_pipeline_orders_group_by_status_and_date_and_time_slot_for_service_location_ids,
        "orders_group_by_date_and_time_slot_for_agent_locations": get_pipeline_orders_group_by_date_and_time_slot_for_service_location_ids,
    }
    return func_map[func_name](*args)


def get_pipeline_orders_group_by_status_and_date_and_time_slot_for_service_location_ids(
    service_location_ids: List[str], ordered_statuses: List[OrderStatusEnum]
):
    return [
        {
            "$match": {
                "service_location_id": {"$in": service_location_ids},
                "order_status.0.status": {"$in": ordered_statuses},
            }
        },
        {"$sort": {"pickup_date_time.start": -1, "time_slot": 1}},
        {"$addFields": {"latest_status": {"$first": "$order_status"}}},
        {
            "$group": {
                "_id": {
                    "latest_status": "$latest_status.status",
                    "pick_up_date": "$pickup_date_time.date",
                    "time_slot": "$time_slot",
                },
                "orders": {"$push": "$$ROOT"},
            }
        },
        {
            "$sort": {
                "_id.latest_status": 1,
                "_id.pick_up_date": -1,
                "_id.time_slot": 1,
            }
        },
    ]


def get_pipeline_orders_group_by_date_and_time_slot_for_service_location_ids(
    service_location_ids: List[str], ordered_statuses: List[OrderStatusEnum]
):
    return [
        {
            "$match": {
                "service_location_id": {"$in": service_location_ids},
                "order_status.0.status": {"$in": ordered_statuses},
            }
        },
        {"$sort": {"pickup_date_time.start": -1, "time_slot": 1}},
        {
            "$group": {
                "_id": {
                    "pick_up_date": "$pickup_date_time.date",
                    "time_slot": "$time_slot",
                },
                "orders": {"$push": "$$ROOT"},
            }
        },
        {
            "$sort": {
                "_id.pick_up_date": -1,
                "_id.time_slot": 1,
            }
        },
    ]


def get_pipeline_orders_by_status_for_service_location_ids(
    service_location_ids: List[str], ordered_statuses: List[OrderStatusEnum]
):
    return [
        {
            "$match": {
                "service_location_id": {"$in": service_location_ids},
                "order_status.0.status": {"$in": ordered_statuses},
            }
        },
        {"$sort": {"pickup_date_time.start": -1, "time_slot": 1}},
    ]


def get_pipeline_service_prices_for_locations(
    service_location_ids: List[str | PyObjectId],
):
    return [
        {
            "$match": {
                "service_location_id": {"$in": service_location_ids},
            }
        },
        {"$sort": {"sort_order": 1}},
        {
            "$group": {
                "_id": {
                    "service_location_id": "$service_location_id",
                    "service_id": "$service_id",
                },
                "prices": {"$push": "$$ROOT"},
            }
        },
    ]
