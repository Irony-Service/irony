from typing import Any, Optional
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import  shared_config


class CallToAction(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    key: Optional[str] = None
    value: Optional[Any] = None

    model_config = shared_config
