from datetime import datetime
from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class Service(BaseModel):
    _id: Optional[ObjectId]
    service_category: str
    service_type: str
    service_name: str
    call_to_action_key: str

    class Config(ModelConfig):
        pass


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
