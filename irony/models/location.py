from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from irony.models.common_model import ModelConfig
from irony.models.user import User


class Location(BaseModel):
    type: Optional[str] = "Point"
    coordinates: List[float] = Field(..., min_items=2, max_items=2)


class UserLocation(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[Location] = None
    url: Optional[str] = None
    created_on: Optional[datetime] = None
    last_used: Optional[datetime] = None

    class Config(ModelConfig):
        pass
