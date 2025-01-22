from pydantic import BaseModel

class UserRegistration(BaseModel):
    mobile: str 
    password: str
    confirm_password: str
