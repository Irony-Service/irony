from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class ModelConfig:
    arbitrary_types_allowed = True


class OrderItem(BaseModel):
    id: ObjectId
    order_id: ObjectId
    service_id: ObjectId
    count: float
    price: float

    class Config(ModelConfig):
        pass
