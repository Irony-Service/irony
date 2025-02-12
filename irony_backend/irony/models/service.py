from enum import Enum
from typing import Optional
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.pyobjectid import PyObjectId


class Service(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    service_category: Optional[str] = None
    service_type: Optional[str] = None
    service_name: Optional[str] = None
    call_to_action_key: Optional[str] = None

    model_config = shared_config


class CategoryEnum(str, Enum):
    LAUNDRY = "LAUNDRY"
    DRYCLEAN = "DRYCLEAN"
    STICHING = "STICHING"


class ServiceEnum(str, Enum):
    IRON = "IRON"
    WASH = "WASH"
    WASH_IRON = "WASH_IRON"
    DRYCLEAN = "DRYCLEAN"
    ROLLING = "ROLLING"
