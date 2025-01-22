from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import CommonModel, shared_config
from typing import Optional


class User(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: Optional[str] = None
    wa_id: Optional[str] = None
    created_on: Optional[datetime] = None

    model_config = shared_config
