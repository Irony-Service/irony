from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import CommonModel, ModelConfig


class OrderItem(BaseModel):
    service_name: Optional[str]
    count: Optional[float]
    price: Optional[float]

    class Config(ModelConfig):
        pass
