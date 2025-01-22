from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.location import UserLocation
from irony.models.order_item import OrderItem
from irony.models.service import Service


class UpdateOrderRequest(BaseModel):
    order_id: str
    current_status: str
    new_status: str
    items: List[OrderItem]
    information: Optional[str] = None
    total_price: Optional[float] = None
    pickup_by: Optional[str] = None

    model_config = shared_config


class UpdateOrderResponseBody(BaseModel):
    parent_order_id: Optional[str] = None
    sub_ids: Optional[List[str]] = None
    sub_id_dict: Optional[dict] = None
    order_ids: Optional[List[str]] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None

    model_config = shared_config


class UpdateOrderResponse(CommonReponse):
    body: Optional[UpdateOrderResponseBody] = None

    model_config = shared_config
