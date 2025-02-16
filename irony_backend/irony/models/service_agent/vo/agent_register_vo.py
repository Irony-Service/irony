from typing import List, Optional
from pydantic import BaseModel


class AgentRegisterRequest(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_ids: Optional[List[str]] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None
