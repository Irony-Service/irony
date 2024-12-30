from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig

class FetchOrderDetailsRequest(BaseModel):
    order_id:  Optional[str] = None;

    class Config(ModelConfig):
        pass

class FetchOrderDetailsResponsebody(BaseModel):
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


class FetchOrderDetailsResponse(BaseModel):
    body: Optional[FetchOrderDetailsResponsebody] = None; # type: ignore
    success: Optional[bool] = None;
    error: Optional[str] = None;

    class Config(ModelConfig):
        pass