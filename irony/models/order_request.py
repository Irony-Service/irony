from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from irony.models.common_model import ModelConfig


class OrderRequest(BaseModel):
    _id: ObjectId = None
    order_id: str = None
    service_location_id: str = None
    distance: float = None
    trigger_time: datetime = None
    is_pending: bool = None
    try_count: int = None

    class Config(ModelConfig):
        pass
