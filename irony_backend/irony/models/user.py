from datetime import datetime
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from typing import Optional


class User(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: Optional[str] = None
    wa_id: Optional[str] = None
    created_on: Optional[datetime] = None

    model_config = shared_config
