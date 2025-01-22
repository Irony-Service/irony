from typing import Any, Optional
from bson import ObjectId
from pydantic import Field

from irony.models.common_model import CommonModel, shared_config


class CallToAction(CommonModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    key: Optional[str] = None
    value: Optional[Any] = None

    model_config = shared_config
