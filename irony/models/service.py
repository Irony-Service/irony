from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import CommonModel, ModelConfig


class Service(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    service_category: Optional[str]
    service_type: Optional[str]
    service_name: Optional[str]
    call_to_action_key: Optional[str]

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
