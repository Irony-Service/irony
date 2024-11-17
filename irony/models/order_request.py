from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

from irony.models.common_model import ModelConfig
from irony.models.order import Order
from irony.models.service_location import DeliveryTypeEnum, ServiceLocation


class OrderRequest(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    order_id: Optional[ObjectId] = None
    order: Optional[Order] = None
    delivery_type: Optional[DeliveryTypeEnum] = None
    delivery_service_locations_ids: Optional[List[ObjectId]] = None
    delivery_service_locations: Optional[List[ServiceLocation]] = None
    service_location_id: Optional[ObjectId] = None
    service_location: Optional[ServiceLocation] = None
    distance: Optional[float] = None
    trigger_time: Optional[datetime] = None
    is_pending: Optional[bool] = None
    try_count: Optional[int] = None

    class Config(ModelConfig):
        pass
