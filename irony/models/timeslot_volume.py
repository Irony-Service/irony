from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Dict, Optional

from irony.models.common_model import CommonModel, shared_config


class TimeslotQuota(BaseModel):
    current: Optional[int] = None
    limit: Optional[int] = None

    model_config = shared_config


class TimeslotVolume(CommonModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    service_loaction_id: Optional[ObjectId] = None
    daily_limit: Optional[int] = None
    current_clothes: Optional[int] = None
    timeslot_distributions: Optional[Dict[str, TimeslotQuota]] = None
    services_distribution: Optional[Dict[str, TimeslotQuota]] = None
    operation_date: Optional[datetime] = None

    model_config = shared_config
