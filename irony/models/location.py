from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from irony.models.common_model import ModelConfig
from irony.models.user import User


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., min_items=2, max_items=2)


class UserLocation(BaseModel):
    _id: Optional[ObjectId] = None
    user: Optional[User] = None
    name: str = None
    address: str = None
    location: Location = None
    url: str = None
    created_on: Optional[datetime] = None
    last_used: Optional[datetime] = None

    class Config(ModelConfig):
        pass
