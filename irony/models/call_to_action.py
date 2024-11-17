from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class CallToAction(BaseModel):
    _id: Optional[ObjectId] = None
    key: Optional[str] = None
    value: Optional[Any] = None

    class Config(ModelConfig):
        pass
