from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from irony.models.common_model import shared_config
from irony.models.pyobjectid import PyObjectId


class Location(BaseModel):
    type: Optional[str] = "Point"
    coordinates: List[float] = Field(..., min_items=2, max_items=2)  # type: ignore
    
    def to_coordinates_string(self) -> str:
        return f"{self.coordinates[0]:.5f},{self.coordinates[1]:.5f}"


class UserLocation(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user: Optional[str] = None
    nickname: Optional[str] = None
    address: Optional[str] = None
    location: Optional[Location] = None
    url: Optional[str] = None
    created_on: Optional[datetime] = None
    last_used: Optional[datetime] = None

    model_config = shared_config
