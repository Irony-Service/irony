from typing import Any
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class CallToAction(BaseModel):
    _id: ObjectId = None
    key: str = None
    value: Any = None

    class Config(ModelConfig):
        pass
