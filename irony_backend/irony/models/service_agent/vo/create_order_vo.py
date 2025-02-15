from typing import List, Optional
from pydantic import BaseModel

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.order_item import OrderItem
from irony.models.pyobjectid import PyObjectId


class CreateOrderRequest(BaseModel):
    user_id: str
    user_wa_id: str
    service_location_id: PyObjectId
    notes: Optional[str] = None
    items: List[OrderItem]
    total_price: float

    model_config = shared_config


class CreateOrderResponse(CommonReponse):
    data: Optional[dict] = None

    model_config = shared_config
