from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from irony.models.common_model import CommonModel, ModelConfig


HUMAN_READABLE_LABELS = {
    "SERVICE_PENDING": "Service Pending",
    "LOCATION_PENDING": "Location Pending",
    "TIME_SLOT_PENDING": "Time Slot Pending",
    "FINDING_IRONMAN": "Finding Ironman",
    "PICKUP_PENDING": "Pickup Pending",
    "PICKUP_USER_NO_RESP": "Pickup User No Response",
    "PICKUP_USER_REJECTED": "Pickup User Rejected",
    "PICKUP_COMPLETE": "Pickup Complete",
    "WORK_IN_PROGRESS": "Work In Progress",
    "WORK_DONE": "Work Done",
    "TO_BE_DELIVERED": "To Be Delivered",
    "DELIVERY_PENDING": "Delivery Pending",
    "DELIVERY_ATTEMPTED": "Delivery Attempted",
    "DELIVERED": "Delivered",
    "CLOSED": "Closed",
}



class OrderStatusEnum(str, Enum):
    SERVICE_PENDING = "SERVICE_PENDING"
    LOCATION_PENDING = "LOCATION_PENDING"
    TIME_SLOT_PENDING = "TIME_SLOT_PENDING"
    FINDING_IRONMAN = "FINDING_IRONMAN"
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

    @staticmethod
    def getHomeSectionLabel(status: "OrderStatusEnum") -> str:
        return HUMAN_READABLE_LABELS.get(status, status)


class OrderStatus(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    order_id: Optional[ObjectId] = None
    status: Optional[OrderStatusEnum] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None

    class Config(ModelConfig):
        pass
