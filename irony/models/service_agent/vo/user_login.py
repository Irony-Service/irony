from pydantic import BaseModel

class UserLogin(BaseModel):
    mobile: str
    password: str
