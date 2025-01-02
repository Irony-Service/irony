from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from irony.models.common_model import ModelConfig


class PickupTime(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    class Config(ModelConfig):
        pass
