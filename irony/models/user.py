from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from .pyObjectId import PyObjectId
from typing import Optional


class ModelConfig:
    arbitrary_types_allowed = True


class User(BaseModel):
    _id: Optional[ObjectId] = None
    name: str
    wa_id: str
    created_on: datetime

    class Config(ModelConfig):
        populate_by_name = True
        arbitrary_types_allowed = True
