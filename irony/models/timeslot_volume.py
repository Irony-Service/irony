from datetime import datetime
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field
from typing import Dict, Optional

from irony.models.common_model import shared_config


class TimeslotQuota(BaseModel):
    current: Optional[int] = None
    limit: Optional[int] = None

    model_config = shared_config


class TimeslotVolume(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    service_loaction_id: Optional[PyObjectId] = None
    daily_limit: Optional[int] = None
    current_clothes: Optional[int] = None
    timeslot_distributions: Optional[Dict[str, TimeslotQuota]] = None
    services_distribution: Optional[Dict[str, TimeslotQuota]] = None
    operation_date: Optional[datetime] = None

    model_config = shared_config
