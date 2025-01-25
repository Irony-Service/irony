from enum import Enum
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.location import Location
from irony.models.timeslot_volume import TimeslotVolume
from irony.models.pyobjectid import PyObjectId


class LocationTypeEnum(str, Enum):
    OWN = "OWN"
    OUTSOURCE = "OUTSOURCE"


class DeliveryTypeEnum(str, Enum):
    DELIVERY = "DELIVERY"
    SELF_PICKUP = "SELF_PICKUP"


def get_delivery_enum_from_string(value: str):
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

    model_config = shared_config


class Service(BaseModel):
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    model_config = shared_config


class ServiceLocation(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: Optional[str] = None
    services: Optional[List[Service]] = None
    time_slots: Optional[List[str]] = None
    coords: Optional[Location] = None
    range: Optional[float] = None
    location_type: Optional[LocationTypeEnum] = None
    delivery_type: Optional[DeliveryTypeEnum] = None
    total_workforce: Optional[float] = None
    is_active: Optional[bool] = None
    rating: Optional[float] = None
    wa_id: Optional[str] = None
    auto_accept: Optional[bool] = None
    distance: Optional[float] = None
    timeslot_volumes: Optional[List[TimeslotVolume]] = None

    model_config = shared_config
