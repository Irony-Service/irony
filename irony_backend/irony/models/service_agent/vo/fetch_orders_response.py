from datetime import datetime

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.order import Order
from irony.models.order_vo import OrderVo


class TimeSlotItem(BaseModel):
    time_slot: Optional[str] = None
    orders: Optional[List[OrderVo]] = None


class DateItem(BaseModel):
    date: Optional[datetime] = None
    time_slots: Optional[List[TimeSlotItem]]


class FetchOrdersResponseDataItem(BaseModel):
    key: Optional[str] = None
    label: Optional[str] = None
    dates: Optional[List[DateItem]] = None


class FetchOrdersResponse(CommonReponse):
    data: Optional[List[FetchOrdersResponseDataItem]] = None

    model_config = shared_config
