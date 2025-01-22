from typing import Optional

from pydantic import BaseModel


class CommonReponse(BaseModel):
    success: Optional[bool] = None
    message: Optional[str] = None
