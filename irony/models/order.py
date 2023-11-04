from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.order_item import OrderItem

class Order(BaseModel):
    id: ObjectId
    user_id: ObjectId
    order_items: list[OrderItem]
    service_location_id: ObjectId
    location: list[tuple[str, str]]
    total_price: float
    total_count: float
    # TODO: wheter to use status_id of embedded object, or make it a list of embedded status objects
    status_id: ObjectId
    is_active: bool
    pickup_agent_id: ObjectId
    drop_agent_id: ObjectId
    created_on: datetime