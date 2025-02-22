from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from irony.models.common_model import shared_config


class PickupDateTime(BaseModel):
    date: Optional[datetime] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    model_config = shared_config
