from typing import Optional

from pydantic import BaseModel


class CommonReponse(BaseModel):
    success: Optional[bool] = None
    error: Optional[str] = None
