from typing import Any, Optional
from bson import ObjectId
from pydantic import Field

from irony.models.common_model import CommonModel, ModelConfig


class CallToAction(CommonModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    key: Optional[str] = None
    value: Optional[Any] = None

    class Config(ModelConfig):
        pass
