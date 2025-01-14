from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional

from irony.models.common_model import CommonModel, ModelConfig
from irony.models.location import UserLocation
from irony.models.order_item import OrderItem
from irony.models.order_status import OrderStatus
from irony.models.pickup_tIme import PickupTime
from irony.models.service import Service
from irony.models.service_location import ServiceLocation
from irony.models.user import User


class Order(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    collected_cloths: Optional[int] = None
    simple_id: Optional[str] = None
    sub_id: Optional[str] = None
    user_id: Optional[ObjectId] = None
    user: Optional[User] = None
    user_wa_id: Optional[str] = None
    order_item: Optional[OrderItem] = None
    service_location_id: Optional[ObjectId] = None
    service_location: Optional[ServiceLocation] = None
    services: Optional[List[Service]] = None
    count_range: Optional[str] = None
    count_range_description: Optional[str] = None
    location: Optional[UserLocation] = None
    existing_location: Optional[bool] = None
    trigger_order_request_at: Optional[datetime] = None
    time_slot: Optional[str] = None
    time_slot_description: Optional[str] = None
    total_price: Optional[float] = None
    total_count: Optional[float] = None
    # TODO: wheter to use status_id of embedded object, or make it a list of embedded status objects
    order_status: Optional[List[OrderStatus]] = None
    is_active: Optional[bool] = None
    pickup_agent_id: Optional[str] = None
    drop_agent_id: Optional[str] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    pick_up_time: Optional[PickupTime] = None
    auto_alloted: Optional[bool] = None
    delivery_type: Optional[str] = None
    maps_link: Optional[str] = None
    preferred_delivery_slot: Optional[str] = None
    picked_up_time: Optional[datetime] = None

    # class Config(ModelConfig):
    #     populate_by_name = True
    #     arbitrary_types_allowed = True
