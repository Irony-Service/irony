from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.service import Service


class ServiceLocation(BaseModel):
    id: ObjectId
    name: str
    # NOTE: using embedded status objects
    services: list[Service]
    node_point: list[tuple[str, str]]
    range: float
    location_type: str
    total_workforce: float
    is_active: bool
    rating: float


class LocationTypeEnum(str, Enum):
    OWN = "OWN"
    OUTSOURCE = "OUTSOURCE"
