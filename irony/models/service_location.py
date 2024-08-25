from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig
from irony.models.location import Location
from irony.models.service import Service, ServiceEntry


class LocationTypeEnum(str, Enum):
    OWN = "OWN"
    OUTSOURCE = "OUTSOURCE"


class ServiceLocation(BaseModel):
    _id: ObjectId = None
    name: str = None
    services: list[ServiceEntry] = None
    coords: Location = None
    range: float = None
    location_type: LocationTypeEnum = None
    total_workforce: float = None
    is_active: bool = None
    rating: float = None
    wa_id: str = None

    class Config(ModelConfig):
        pass
