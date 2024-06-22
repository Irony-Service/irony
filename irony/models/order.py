from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional

from irony.models.order_item import OrderItem
from .pyObjectId import PyObjectId


class ModelConfig:
    arbitrary_types_allowed = True


class Order(BaseModel):
    _id: Optional[ObjectId] = None
    user_id: Optional[ObjectId] = None
    count_range: Optional[str] = None
    order_items: Optional[list[OrderItem]] = None
    service_location_id: Optional[ObjectId] = None
    location: Optional[list[tuple[str, str]]] = None
    total_price: Optional[float] = None
    total_count: Optional[float] = None
    # TODO: wheter to use status_id of embedded object, or make it a list of embedded status objects
    status_id: Optional[ObjectId] = None
    is_active: Optional[bool] = None
    pickup_agent_id: Optional[ObjectId] = None
    drop_agent_id: Optional[ObjectId] = None
    created_on: Optional[datetime] = None

    class Config(ModelConfig):
        populate_by_name = True
        arbitrary_types_allowed = True
