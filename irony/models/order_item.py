from typing import Optional
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class OrderItem(BaseModel):
    # id: Optional[ObjectId] = None
    # order_id: Optional[ObjectId]
    service_id: Optional[ObjectId]
    count: Optional[float]
    price: Optional[float]

    class Config(ModelConfig):
        pass
