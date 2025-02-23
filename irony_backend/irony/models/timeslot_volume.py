from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.pyobjectid import PyObjectId


class Quota(BaseModel):
    current: int
    limit: int

    model_config = shared_config


class TimeslotVolume(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    service_location_id: Optional[PyObjectId] = None
    daily_limit: int
    current_clothes: int
    timeslot_distributions: Optional[Dict[str, Quota]] = None
    services_distribution: Optional[Dict[str, Quota]] = None
    operation_date: Optional[datetime] = None

    model_config = shared_config
