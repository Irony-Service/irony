from datetime import datetime
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field
from typing import Dict, Optional

from irony.models.common_model import shared_config


class Quota(BaseModel):
    current: Optional[int] = None
    limit: Optional[int] = None

    model_config = shared_config


class TimeslotVolume(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    service_location_id: Optional[PyObjectId] = None
    daily_limit: Optional[int] = None
    current_clothes: Optional[int] = None
    timeslot_distributions: Optional[Dict[str, Quota]] = None
    services_distribution: Optional[Dict[str, Quota]] = None
    operation_date: Optional[datetime] = None

    model_config = shared_config
