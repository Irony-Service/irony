from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from irony.models.common_model import ModelConfig
from irony.models.service_location import DeliveryTypeEnum


class OrderRequest(BaseModel):
    _id: Optional[ObjectId] = None
    order_id: Optional[ObjectId] = None
    delivery_type: Optional[DeliveryTypeEnum] = None
    delivery_service_locations_ids: Optional[List[ObjectId]] = None
    service_location_id: Optional[ObjectId] = None
    distance: Optional[float] = None
    trigger_time: Optional[datetime] = None
    is_pending: Optional[bool] = None
    try_count: Optional[int] = None

    class Config(ModelConfig):
        pass
