from datetime import datetime

from irony.models.order import Order
from irony.models.order_status_enum import OrderStatusEnum


def get_pipeline_geo_near_service_locations_for_order(
    order: Order, geo_near_radius: int
):
    return [
        {
            "$geoNear": {
                "key": "coords",
                "near": {
                    "type": "Point",
                    "coordinates": order.location.location.coordinates,  # type: ignore
                },
                "distanceField": "distance",
                "maxDistance": geo_near_radius,
                "spherical": True,
            }
        },
        {
            "$match": {
                "$expr": {
                    "$gte": [
                        "$range",
                        "$distance",
                    ]  # Filter where range is greater or equal to distance
                },
                "service_ids": {"$all": [service.id for service in order.services]},  # type: ignore
                "time_slots": {"$in": [order.time_slot]},
            }
        },
        {
            "$lookup": {
                "from": "timeslot_volume",  # the collection to join
                "localField": "_id",  # field in orders referencing service_locations._id
                "foreignField": "service_location_id",  # field in service_locations to match
                "as": "timeslot_volumes",  # output array field for matched documents
            }
        },
        {
            "$group": {
                "_id": "$delivery_type",  # Group by the "category" field
                "documents": {
                    "$push": "$$ROOT"
                },  # Push the entire document into the "documents" array
            }
        },
        {"$sort": {"distance": 1}},
        {"$limit": 25},
    ]


def get_pipeline_pending_orders_requests(current_time: datetime, try_count: int = 3):
    return [
        {
            "$match": {
                "trigger_time": {"$lt": current_time},
                "is_pending": True,
                "try_count": {"$lt": try_count},
            }
        },
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "service_location_id",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match
                "as": "service_location",  # output array field for matched documents
            }
        },
        {
            "$unwind": "$service_location"  # flatten if each order has only one service location
        },
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "delivery_service_locations_ids",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match
                "as": "delivery_service_locations",  # output array field for matched documents
            }
        },
        {
            "$lookup": {
                "from": "order",  # the collection to join
                "localField": "order_id",
                "foreignField": "_id",
                "as": "order",
            }
        },
        {"$unwind": "$order"},  # flatten if each order has only one order
    ]


def get_pipeline_is_ironman_delivery_schedule_pending(trigger_time_str: str):
    return [
        {
            "$match": {
                "start_time": {"$lte": trigger_time_str},
                "group": "TIME_SLOT_ID",
                "is_delivery_schedule_pending": True,
            }
        }
    ]


def get_pipeline_ironman_delivery_schedule(pending_schedule_key: str):
    return [
        {
            "$match": {
                "time_slot": pending_schedule_key,
                "order_status.0.status": {
                    "$in": [
                        OrderStatusEnum.PICKUP_PENDING,
                        OrderStatusEnum.DELIVERY_PENDING,
                    ]
                },
            }
        },
        {
            "$lookup": {
                "from": "user",  # the collection to join
                "localField": "user_id",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match`
                "as": "user",  # output array field for matched documents
            }
        },
        {"$unwind": "$user"},
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "service_location_id",  # field in orders referencing service_locations._id`
                "foreignField": "_id",  # field in service_locations to match
                "as": "service_location",  # output array field for matched documents
            }
        },
        {"$unwind": "$service_location"},
        {"$sort": {"distance": 1}},
        {
            "$group": {
                "_id": "$service_location_id",
                "documents": {
                    "$push": "$$ROOT"
                },  # Push the entire document into the "documents" list
            }
        },
    ]


def get_pipeline_is_work_schedule_pending(trigger_time: str):
    return [
        {
            "$match": {
                "end_time": {"$lte": trigger_time},
                "is_work_schedule_pending": True,
            }
        }
    ]


def get_pipeline_pending_work_schedule(
    pending_schedule_key, start_datetime, end_datetime
):
    return [
        {
            "$match": {
                "time_slot": pending_schedule_key,
                "order_status.0.status": {
                    "$in": [
                        OrderStatusEnum.PICKUP_COMPLETE,
                        OrderStatusEnum.WORK_IN_PROGRESS,
                    ]
                },
                "updated_on": {"$gte": start_datetime, "$lte": end_datetime},
            }
        },
        {
            "$lookup": {
                "from": "user",  # the collection to join
                "localField": "user_id",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match`
                "as": "user",  # output array field for matched documents
            }
        },
        {"$unwind": "$user"},
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "service_location_id",  # field in orders referencing service_locations._id`
                "foreignField": "_id",  # field in service_locations to match
                "as": "service_location",  # output array field for matched documents
            }
        },
        {"$unwind": "$service_location"},
        {"$sort": {"distance": 1}},
        {
            "$group": {
                "_id": "$service_location_id",
                "documents": {
                    "$push": "$$ROOT"
                },  # Push the entire document into the "documents" list
            }
        },
    ]


def get_pipeline_ironman_work_schedule(pending_schedule_key: str):
    """Get MongoDB pipeline for ironman work schedule.

    Args:
        pending_schedule_key: Time slot key from pending schedule

    Returns:
        List of pipeline stages for MongoDB aggregation
    """
    return [
        {
            "$match": {
                "service_location_id": {"$ne": None},
                "time_slot": pending_schedule_key,
                "order_status.0.status": {
                    "$in": [
                        OrderStatusEnum.PICKUP_COMPLETE,
                        OrderStatusEnum.WORK_IN_PROGRESS,
                    ]
                },
            }
        },
        {
            "$lookup": {
                "from": "user",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
        {
            "$lookup": {
                "from": "service_locations",
                "localField": "service_location_id",
                "foreignField": "_id",
                "as": "service_location",
            }
        },
        {"$unwind": "$service_location"},
        {"$sort": {"distance": 1}},
        {
            "$group": {
                "_id": "$service_location_id",
                "documents": {"$push": "$$ROOT"},
            }
        },
    ]


def get_pipeline_work_schedule_pending(trigger_time: str):
    """Get pipeline for finding pending work schedules.

    Args:
        trigger_time: Time to check against end_time

    Returns:
        Pipeline stages for MongoDB aggregation
    """
    return [
        {
            "$match": {
                "end_time": {"$lte": trigger_time},
                "is_work_schedule_pending": True,
            }
        }
    ]


def get_pipeline_is_pending_work_schedule_pending(trigger_time: str):
    """Get pipeline for finding pending schedules.

    Args:
        trigger_time: Time to check against start_time

    Returns:
        Pipeline stages for MongoDB aggregation
    """
    return [
        {
            "$match": {
                "start_time": {"$lte": trigger_time},
                "is_pending_schedule_pending": True,
            }
        }
    ]


def get_pipeline_pending_orders_create_requests(current_time: datetime):
    """Get pipeline for finding pending orders to create requests.

    Args:
        current_time: Current datetime

    Returns:
        Pipeline stages for MongoDB aggregation
    """
    return [
        {
            "$match": {
                "trigger_order_request_at": {"$lte": current_time},
                "trigger_order_request_pending": True,
            }
        },
    ]


def get_pipeline_missed_schedule_slots(formatted_time: str):
    """Get pipeline for finding missed schedule slots.

    Args:
        formatted_time: Formatted time string

    Returns:
        Pipeline stages for MongoDB aggregation
    """
    return [{"$match": {"end_time": {"$eq": formatted_time}, "group": "TIME_SLOT_ID"}}]


def get_pipeline_missed_orders(start_of_today: datetime, current_time: datetime):
    """Get pipeline for finding missed orders.

    Args:
        start_of_today: Start of current day
        current_time: Current datetime

    Returns:
        Pipeline stages for MongoDB aggregation
    """
    return [
        {
            "$match": {
                "order_status.0.status": {"$in": [OrderStatusEnum.PICKUP_PENDING]},
                "pickup_date_time.end": {"$gte": start_of_today, "$lte": current_time},
            }
        },
    ]


def get_pipeline_timeslot_volume_archive(end_of_yesterday: datetime):
    """Get pipeline for archiving timeslot volumes.

    Args:
        end_of_yesterday: End of previous day

    Returns:
        Pipeline stages for MongoDB aggregation
    """
    return [{"$match": {"operation_date": {"$lt": end_of_yesterday}}}]
