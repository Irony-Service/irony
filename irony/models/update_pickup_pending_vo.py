from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig
from irony.models.location import UserLocation
from irony.models.order_item import OrderItem
from irony.models.service import Service

class UpdateOrderRequest(BaseModel):
    order_id:  Optional[str] = None;
    current_status: Optional[str] = None;
    new_status: Optional[str] = None;
    items: Optional[List[OrderItem]] = None;
    information: Optional[str] = None;
    total_price: Optional[float] = None;
    pickup_by: Optional[str] = None;
    preferred_delivey_slot: Optional[str] = None;

    
    class Config(ModelConfig):
        pass

class UpdateOrderResponseBody(BaseModel):
    parent_order_id:  Optional[str] = None;
    sub_ids: Optional[List[str]] = None;
    order_ids: Optional[List[str]] = None;
    service_name: Optional[str] = None;
    status: Optional[str] = None;
    expected_delivery_date: Optional[str] = None;
    price: Optional[float] = None;
    location :Optional[UserLocation]= None;

    class Config(ModelConfig):
        pass
class UpdateOrderResponse(BaseModel):
    body: Optional[UpdateOrderResponseBody] = None; # type: ignore
    success: Optional[bool] = None;
    error: Optional[str] = None;

    class Config(ModelConfig):
        pass
    