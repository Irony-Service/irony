from typing import Dict, List, Optional
from pydantic import BaseModel

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.order_item import OrderItem
from irony.models.pyobjectid import PyObjectId


class CommonOrderRequest(BaseModel):
    items: List[OrderItem]
    total_price: float
    notes: Optional[str] = None

    model_config = shared_config


class CommonOrderResponseBody(BaseModel):
    sub_id_dict: Optional[Dict] = None
    order_ids: Optional[List[str]] = None

    model_config = shared_config


class CommonOrderResponse(CommonReponse):
    data: Optional[CommonOrderResponseBody] = None
    model_config = shared_config
