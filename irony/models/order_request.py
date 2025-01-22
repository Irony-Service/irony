from typing import List, Optional, Union
from pydantic import Field
from datetime import datetime
from bson import ObjectId

from irony.models.common_model import CommonModel, shared_config
from irony.models.order import Order
from irony.models.service_location import DeliveryTypeEnum, ServiceLocation
from irony.models.timeslot_volume import TimeslotVolume


class OrderRequest(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    order_id: Optional[ObjectId] = None
    order: Optional[Order] = None
    delivery_type: Optional[DeliveryTypeEnum] = None
    delivery_service_locations_ids: Optional[List[Union[ObjectId, None]]] = None
    delivery_service_locations: Optional[List[ServiceLocation]] = None
    service_location_id: Optional[ObjectId] = None
    service_location: Optional[ServiceLocation] = None
    distance: Optional[float] = None
    trigger_time: Optional[datetime] = None
    is_pending: Optional[bool] = None
    try_count: Optional[int] = None
    timeslot_volumes: Optional[List[TimeslotVolume]] = None

    model_config = shared_config
