from typing import Dict, List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig


class FetchOrderRequest(BaseModel):
    service_location: Optional[str] = None

    class Config(ModelConfig):
        pass


class OrderChunk(BaseModel):
    order_id: Optional[str] = Field(default=None, alias="_id")
    simple_id: Optional[str] = None
    service_name: Optional[str] = None
    clothes_count: Optional[str] = None
    pickup_time: Optional[str] = None

    class Config(ModelConfig):
        pass


class FetchOrderResponseBody(BaseModel):
    pending_pick_up: Optional[List[OrderChunk]] = None
    work_in_progress: Optional[List[OrderChunk]] = None
    delivery_pending: Optional[List[OrderChunk]] = None

    class Config(ModelConfig):
        pass


class FetchOrdersResponseBodyItem(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    orders: Optional[List[OrderChunk]] = None


class FetchOrdersResponse(BaseModel):
    body: Optional[Dict[str, List[OrderChunk]]] = None
    success: Optional[bool] = None
    error: Optional[str] = None

    class Config(ModelConfig):
        pass
