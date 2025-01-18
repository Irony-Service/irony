from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from irony.models.common_model import ModelConfig


class PickupDateTime(BaseModel):
    date: Optional[datetime] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    class Config(ModelConfig):
        pass
