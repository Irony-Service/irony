from pydantic import BaseModel, Field

class UserLogin(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)
    password: str
