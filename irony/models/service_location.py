from datetime import datetime
from enum import Enum
from typing import List
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig
from irony.models.location import Location
from irony.models.service import Service


class LocationTypeEnum(str, Enum):
    OWN = "OWN"
    OUTSOURCE = "OUTSOURCE"


class DeliveryTypeEnum(str, Enum):
    DELIVERY = "DELIVERY"
    SELF_PICKUP = "SELF_PICKUP"


class ServiceEntry(BaseModel):
    id: ObjectId
    service_location_id: ObjectId
    service_id: ObjectId
    rate: float
    discount: float
    daily_piece_limit: int
    assigned_pieces_today: int = 0
    workforce: float
    is_active: bool
    referral_discount: float

    class Config(ModelConfig):
        pass


class ServiceLocation(BaseModel):
    _id: ObjectId = None
    name: str = None
    services: List[ServiceEntry] = None
    coords: Location = None
    range: float = None
    location_type: LocationTypeEnum = None
    delivery_type: DeliveryTypeEnum = None
    total_workforce: float = None
    is_active: bool = None
    rating: float = None
    wa_id: str = None

    class Config(ModelConfig):
        pass
