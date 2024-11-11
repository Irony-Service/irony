from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig
from .pyObjectId import PyObjectId
from typing import Optional


class User(BaseModel):
    _id: Optional[ObjectId] = None
    name: str
    wa_id: str
    created_on: datetime

    class Config(ModelConfig):
        pass
