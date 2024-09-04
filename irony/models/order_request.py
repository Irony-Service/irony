from typing import List
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from irony.models.common_model import ModelConfig
from irony.models.service_location import DeliveryTypeEnum


class OrderRequest(BaseModel):
    _id: ObjectId = None
    order_id: ObjectId = None
    delivery_type: DeliveryTypeEnum = None
    delivery_service_locations_ids: List[ObjectId] = None
    service_location_id: ObjectId = None
    distance: float = None
    trigger_time: datetime = None
    is_pending: bool = None
    try_count: int = None

    class Config(ModelConfig):
        pass
