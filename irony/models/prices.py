from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

from irony.models.common_model import shared_config
from irony.models.order import Order
from irony.models.service import Service
from irony.models.service_location import DeliveryTypeEnum, ServiceLocation
from irony.models.timeslot_volume import TimeslotVolume
from enum import Enum


class CategoryKeyEnum(str, Enum):
    ONE_BY_FOUR = "1/4"
    TWO_BY_FOUR = "2/4"
    THREE_BY_FOUR = "3/4"
    THREE_HALF_BY_FOUR = "3.5/4"
    FOUR_BY_FOUR = "4/4"
    SPECIAL = "Special"


class Prices(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    service_location_id: Optional[ObjectId] = None
    service_id: Optional[ObjectId] = None
    category_key: Optional[CategoryKeyEnum] = None
    category: Optional[str] = None
    price: Optional[float] = None
    sort_order: Optional[int] = None

    model_config = shared_config
