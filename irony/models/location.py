from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ModelConfig:
    arbitrary_types_allowed = True


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float]


class UserLocation(BaseModel):
    _id: Optional[ObjectId] = None
    user: Optional[str] = None
    name: str = None
    address: str = None
    location: Location = None
    url: str = None
    last_used: Optional[datetime] = None

    class Config(ModelConfig):
        pass
