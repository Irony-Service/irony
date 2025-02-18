from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from irony.models.common_model import shared_config
from irony.models.common_response import CommonReponse
from irony.models.order_vo import OrderVo


class TimeSlotItem(BaseModel):
    """
    Represents a time slot with associated orders.

    Attributes:
        time_slot (str): The time slot identifier
        orders (List[OrderVo]): List of orders in this time slot
    """

    time_slot: Optional[str] = None
    orders: Optional[List[OrderVo]] = None


class DateItem(BaseModel):
    """
    Represents a date with its associated time slots.

    Attributes:
        date (datetime): The date
        time_slots (List[TimeSlotItem]): List of time slots for this date
    """

    date: Optional[datetime] = None
    time_slots: Optional[List[TimeSlotItem]]


class FetchOrdersResponseDataItem(BaseModel):
    """
    Represents a group of orders organized by date.

    Attributes:
        key (str): Unique identifier for the group
        label (str): Display label for the group
        dates (List[DateItem]): List of dates with their orders
    """

    key: Optional[str] = None
    label: Optional[str] = None
    dates: Optional[List[DateItem]] = None


class FetchOrdersResponse(CommonReponse):
    """
    Response model for fetching orders, extending CommonResponse.

    Attributes:
        data (List[FetchOrdersResponseDataItem]): List of order groups
    """

    data: Optional[List[FetchOrdersResponseDataItem]] = None

    model_config = shared_config
