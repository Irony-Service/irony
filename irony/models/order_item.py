from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config


class OrderItem(BaseModel):
    price_id: str
    count: float
    amount: float

    model_config = shared_config
