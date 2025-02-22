from datetime import datetime
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field
from typing import Optional
from irony.models.common_model import shared_config
from irony.models.pyobjectid import PyObjectId


class OrderStatus(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    order_id: Optional[PyObjectId] = None
    status: Optional[OrderStatusEnum] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None

    model_config = shared_config
