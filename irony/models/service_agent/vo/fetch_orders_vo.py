from datetime import datetime

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.order import Order
from irony.models.order_vo import OrderVo


class FetchOrderRequest(BaseModel):
    service_location: Optional[str] = None

    model_config = shared_config


class OrderChunk(BaseModel):
    order_id: Optional[str] = Field(default=None, alias="_id")
    simple_id: Optional[str] = None
    service_name: Optional[str] = None
    clothes_count: Optional[str] = None
    pickup_time: Optional[str] = None

    model_config = shared_config


class FetchOrderResponseBody(BaseModel):
    pending_pick_up: Optional[List[OrderChunk]] = None
    work_in_progress: Optional[List[OrderChunk]] = None
    delivery_pending: Optional[List[OrderChunk]] = None

    model_config = shared_config


class TimeSlotItem(BaseModel):
    time_slot: Optional[str] = None
    orders: Optional[List[OrderVo]] = None


class DateItem(BaseModel):
    date: Optional[datetime] = None
    time_slots: Optional[List[TimeSlotItem]]


class FetchOrdersResponseBodyItem(BaseModel):
    key: Optional[str] = None
    label: Optional[str] = None
    dates: Optional[List[DateItem]] = None


class FetchOrdersResponseBodyItem2(BaseModel):
    key: Optional[str] = None
    label: Optional[str] = None
    orders: Optional[List[Order]] = None


class FetchOrdersResponse(CommonReponse):
    # {"pending_pick_up": {"value":"Pickup", orders:[]}, "work_in_progress":  {"value":"Work In Progress", orders:[]}, "delivery_pending":  {"value":"Delivery", orders:[]}}
    # body: Optional[Dict[str, FetchOrdersResponseBodyItem]] = None
    body: Optional[List[FetchOrdersResponseBodyItem]] = None

    model_config = shared_config
