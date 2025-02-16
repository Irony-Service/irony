from typing import List, Optional
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.location import UserLocation
from irony.models.order_item import OrderItem
from irony.models.service import Service
from irony.models.service_agent.vo.order_request_vo import (
    CommonOrderRequest,
    CommonOrderResponse,
)


class UpdateOrderRequest(CommonOrderRequest):
    order_id: str
    current_status: str
    new_status: str
    location_nickname: Optional[str] = None
    pickup_by: Optional[str] = None

    model_config = shared_config


class UpdateOrderResponse(CommonOrderResponse):
    model_config = shared_config
