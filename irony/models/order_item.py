from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class OrderItem(BaseModel):
    id: ObjectId
    order_id: ObjectId
    service_id: ObjectId
    count: float
    price: float

    class Config(ModelConfig):
        pass
