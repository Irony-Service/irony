from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ModelConfig:
    arbitrary_types_allowed = True


class Location(BaseModel):
    _id: Optional[ObjectId] = None
    user: Optional[ObjectId] = None
    name: str = None
    address: str = None
    location: list[tuple[str, str]] = None
    url: str = None
    last_used: Optional[datetime] = None

    class Config(ModelConfig):
        pass
