from typing import List, Optional

from pydantic import BaseModel, Field

from irony.models.common_model import shared_config
from irony.models.pyobjectid import PyObjectId


class ServiceAgent(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_ids: Optional[List[PyObjectId]] = None
    password: str = Field(exclude=True)

    model_config = shared_config
