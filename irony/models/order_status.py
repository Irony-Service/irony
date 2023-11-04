from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

class OrderStatus(BaseModel):
    id: ObjectId
    order_id: ObjectId
    status : str
    created_on : datetime
    updated_on : datetime
    
class StatusEnum(str, Enum):
    PICKUP_PENDING = "PICKUP_PENDING"
    PICKUP_USER_NO_RESP = "PICKUP_USER_NO_RESP"
    PICKUP_COMPLETE = "PICKUP_COMPLETE"
    WORK_IN_PROGRESS = "WORK_IN_PROGRESS"
    WORK_DONE = "WORK_DONE"
    TO_BE_DELIVERED = "TO_BE_DELIVERED"
    DELIVERY_PENDING = "DELIVERY_PENDING"
    DELIVERY_ATTEMPTED = "DELIVERY_ATTEMPTED"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"