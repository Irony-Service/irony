from typing import Optional

from pydantic import BaseModel


class CommonReponse(BaseModel):
    success: Optional[bool] = True
    message: Optional[str] = None
