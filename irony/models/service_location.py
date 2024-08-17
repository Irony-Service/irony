from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.location import Location
from irony.models.service import Service


class ModelConfig:
    arbitrary_types_allowed = True


class LocationTypeEnum(str, Enum):
    OWN = "OWN"
    OUTSOURCE = "OUTSOURCE"


class ServiceLocation(BaseModel):
    _id: ObjectId = None
    name: str = None
    services: list[Service] = None
    coords: Location = None
    range: float = None
    location_type: LocationTypeEnum = None
    total_workforce: float = None
    is_active: bool = None
    rating: float = None
    wa_id: str = None

    class Config(ModelConfig):
        pass
