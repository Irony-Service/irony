from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import CommonModel, ModelConfig


class Service(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    service_category: Optional[str] = None
    service_type: Optional[str] = None
    service_name: Optional[str] = None
    call_to_action_key: Optional[str] = None

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
