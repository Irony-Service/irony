from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

from irony.models.service import Service


class Referal(BaseModel):
    id: ObjectId
    service_ids: list[Service]
    user_id: ObjectId
    to: str
    referal_code: str
    times_used: int
    max_times: int
