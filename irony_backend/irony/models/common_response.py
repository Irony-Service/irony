from typing import Optional

from pydantic import BaseModel


class CommonReponse(BaseModel):
    """
    Base response model for API responses.

    Attributes:
        success (bool): Indicates if the request was successful
        message (str): Optional message providing additional information about the response
    """

    success: Optional[bool] = True
    message: Optional[str] = None
