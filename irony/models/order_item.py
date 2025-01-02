from typing import Optional
from bson import ObjectId
from pydantic import Field

from irony.models.common_model import CommonModel, ModelConfig


class OrderItem(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    order_id: Optional[ObjectId] = None
    service_id: Optional[ObjectId] = None
    count: Optional[float] = None
    price: Optional[float] = None

    class Config(ModelConfig):
        pass
