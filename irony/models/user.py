from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig
from typing import Optional


class User(BaseModel):
    _id: Optional[ObjectId] = None
    name: Optional[str] = None
    wa_id: Optional[str] = None
    created_on: Optional[datetime] = None

    class Config(ModelConfig):
        pass
