from typing import List, Optional
from pydantic import BaseModel

from irony.models.common_model import shared_config
from irony.models.service import Service


class FetchOrderDetailsRequest(BaseModel):
    order_id: Optional[str] = None

    model_config = shared_config


class FetchOrderDetailsResponsebody(BaseModel):
    order_id: Optional[str] = None
    simple_id: Optional[str] = None
    name: Optional[str] = None
    phone_number: Optional[str] = None
    count_range: Optional[str] = None
    location: Optional[str] = None
    service_location_id: Optional[str] = None
    services: Optional[List[Service]] = None
    pickup_time_start: Optional[str] = None
    pickup_time_end: Optional[str] = None
    time_slot: Optional[str] = None
    status: Optional[str] = None

    model_config = shared_config


class FetchOrderDetailsResponse(BaseModel):
    body: Optional[FetchOrderDetailsResponsebody] = None
    # type: ignore
    success: Optional[bool] = None
    error: Optional[str] = None

    model_config = shared_config
