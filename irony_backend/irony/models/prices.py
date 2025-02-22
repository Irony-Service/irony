from typing import Optional
from pydantic import BaseModel, Field
from irony.models.pyobjectid import PyObjectId

from irony.models.common_model import shared_config
from enum import Enum


class CategoryKeyEnum(str, Enum):
    ONE_BY_FOUR = "1/4"
    TWO_BY_FOUR = "2/4"
    THREE_BY_FOUR = "3/4"
    THREE_HALF_BY_FOUR = "3.5/4"
    FOUR_BY_FOUR = "4/4"
    SPECIAL = "Special"


class Prices(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    service_location_id: Optional[PyObjectId] = None
    service_id: Optional[PyObjectId] = None
    category_key: Optional[CategoryKeyEnum] = None
    category: Optional[str] = None
    price: Optional[float] = None
    sort_order: Optional[int] = None

    model_config = shared_config
