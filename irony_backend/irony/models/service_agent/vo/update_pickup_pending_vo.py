from typing import List, Optional
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
    location_nickname: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    information: Optional[str] = None
    total_price: Optional[float] = None
    pickup_by: Optional[str] = None

    model_config = shared_config


class UpdateOrderResponseBody(BaseModel):
    sub_id_dict: Optional[dict] = None
    order_ids: Optional[List[str]] = None

    model_config = shared_config


class UpdateOrderResponse(CommonReponse):
    data: Optional[UpdateOrderResponseBody] = None

    model_config = shared_config
