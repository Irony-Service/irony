from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel

from irony.models.service import Service


class Referal(BaseModel):
    id: PyObjectId
    service_ids: list[Service]
    user_id: PyObjectId
    to: str
    referal_code: str
    times_used: int
    max_times: int
