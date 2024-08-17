from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class ModelConfig:
    arbitrary_types_allowed = True


class Service(BaseModel):
    id: ObjectId
    service_location_id: ObjectId
    category: str
    service: str
    rate: float
    discount: float
    daily_piece_limit: float
    workforce: float
    is_active: bool
    referral_discount: float

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
