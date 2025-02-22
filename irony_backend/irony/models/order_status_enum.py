from enum import Enum
from typing import Optional

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
DELIVERY_LABELS = {
    "PICKUP_PENDING": "Pickup",
    "DELIVERY_PENDING": "Drop",
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
    def getHomeSectionLabel(status: "Optional[OrderStatusEnum]") -> str:
        if status is None:
            return "Unknown"
        return HUMAN_READABLE_LABELS.get(status, status)

    @staticmethod
    def getDeliveryType(status: "Optional[OrderStatusEnum]") -> str:
        if status is None:
            return "Unknown"
        return DELIVERY_LABELS.get(status, status)
