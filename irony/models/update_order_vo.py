from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig
from irony.models.order_item import OrderItem

class UpdateOrderRequest(BaseModel):
    order_id:  Optional[str] = None;
    current_status: Optional[str] = None;
    new_status: Optional[str] = None;
    items: Optional[List[OrderItem]] = None;
    information: Optional[str] = None;
    total_price: Optional[float] = None;
    pickup_by: Optional[str] = None;
    
    class Config(ModelConfig):
        pass

class UpdateOrderResponseBody(BaseModel):
    order_id:  Optional[str] = None;
    simple_id: Optional[str] = None;
    name : Optional[str] = None;
    phone_number : Optional[str] = None;
    count_range: Optional[str] = None;
    location: Optional[str] = None;
    service_name: Optional[str] = None;
    pickup_time_start: Optional[str] = None;
    pickup_time_end: Optional[str] = None;
    time_slot: Optional[str] = None;
    status: Optional[str] = None;

    class Config(ModelConfig):
        pass
class UpdateOrderResponse(BaseModel):
    body: Optional[UpdateOrderResponseBody] = None; # type: ignore
    success: Optional[bool] = None;
    error: Optional[str] = None;

    class Config(ModelConfig):
        pass
    