from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class ModelConfig:
    arbitrary_types_allowed = True


class OrderStatus(BaseModel):
    id: ObjectId = None
    order_id: ObjectId = None
    status: str = None
    created_on: datetime = None
    updated_on: datetime = None

    class Config(ModelConfig):
        pass


class OrderStatusEnum(str, Enum):
    LOCATION_PENDING = "LOCATION_PENDING"
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
