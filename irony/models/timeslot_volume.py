from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional

from irony.models.common_model import ModelConfig
from irony.models.location import UserLocation
from irony.models.order_item import OrderItem
from irony.models.order_status import OrderStatus
from irony.models.pickup_tIme import PickupTime
from irony.models.service import Service
from irony.models.service_location import ServiceLocation
from irony.models.user import User
from .pyObjectId import PyObjectId


class TimeSlot(BaseModel):
    Current_cloths:Optional[int] = None
    Limit :Optional[int] = None
    class Config(ModelConfig):
        pass

class TimeSlots(BaseModel):
    timeslot_id: Optional[TimeSlot] = None
    class Config(ModelConfig):
        pass
    
class TimeslotVolume(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    service_loaction_id: Optional[ObjectId] = None
    daily_limit: Optional[int] = None
    current_cloths: Optional[int] = None
    timeslot_distributions: Optional[TimeSlots] = None
    operation_date: Optional[datetime] = None
    class Config(ModelConfig):
        pass