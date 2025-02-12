from pydantic import BaseModel

from irony.models.common_model import shared_config


class OrderItem(BaseModel):
    price_id: str
    count: float
    amount: float

    model_config = shared_config
