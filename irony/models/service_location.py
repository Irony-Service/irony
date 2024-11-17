from datetime import datetime
from enum import Enum
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig
from irony.models.location import Location
from irony.models.service import Service


class LocationTypeEnum(str, Enum):
    OWN = "OWN"
    OUTSOURCE = "OUTSOURCE"


class DeliveryTypeEnum(str, Enum):
    DELIVERY = "DELIVERY"
    SELF_PICKUP = "SELF_PICKUP"


def get_delivery_enum_from_string(value):
    return DeliveryTypeEnum.__members__.get(value.upper(), DeliveryTypeEnum.DELIVERY)


class ServiceEntry(BaseModel):
    service_location_id: Optional[ObjectId] = None
    service_id: Optional[ObjectId] = None
    rate: Optional[float] = None
    discount: Optional[float] = None
    daily_piece_limit: Optional[int] = None
    assigned_pieces_today: Optional[int] = 0
    workforce: Optional[float] = None
    is_active: Optional[bool] = None
    referral_discount: Optional[float] = None

    class Config(ModelConfig):
        pass


class ServiceLocation(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: Optional[str] = None
    services: Optional[List[ServiceEntry]] = None
    coords: Optional[Location] = None
    range: Optional[float] = None
    location_type: Optional[LocationTypeEnum] = None
    delivery_type: Optional[DeliveryTypeEnum] = None
    total_workforce: Optional[float] = None
    is_active: Optional[bool] = None
    rating: Optional[float] = None
    wa_id: Optional[str] = None

    class Config(ModelConfig):
        pass
