from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import  shared_config


class CallToAction(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    key: Optional[str] = None
    value: Optional[Any] = None

    model_config = shared_config
