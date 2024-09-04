from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class OrderStatusEnum(str, Enum):
    SERVICE_PENDING = "SERVICE_PENDING"
    LOCATION_PENDING = "LOCATION_PENDING"
    TIME_SLOT_PENDING = "TIME_SLOT_PENDING"
    PICKUP_PENDING = "PICKUP_PENDING"
    PICKUP_USER_NO_RESP = "PICKUP_USER_NO_RESP"
    PICKUP_USER_REJECTED = "PICKUP_USER_REJECTED"
    PICKUP_COMPLETE = "PICKUP_COMPLETE"
    WORK_IN_PROGRESS = "WORK_IN_PROGRESS"
    WORK_DONE = "WORK_DONE"
    TO_BE_DELIVERED = "TO_BE_DELIVERED"
    DELIVERY_PENDING = "DELIVERY_PENDING"
    DELIVERY_ATTEMPTED = "DELIVERY_ATTEMPTED"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"


class OrderStatus(BaseModel):
    _id: ObjectId = None
    order_id: ObjectId = None
    status: OrderStatusEnum = None
    created_on: datetime = None
    updated_on: datetime = None

    class Config(ModelConfig):
        pass
