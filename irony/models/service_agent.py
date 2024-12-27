from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from bson import ObjectId

# from irony.models.common_model import ModelConfig

class ModelConfig:
    arbitrary_types_allowed = True

class ServiceAgent(BaseModel):
    id: Optional[Union[ObjectId,str]] = Field(None, alias='_id')
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_id: Optional[Union[ObjectId,str]] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None


    @field_validator("id", "service_location_id", mode="before")
    def validate_object_id(cls, value):
        if isinstance(value, ObjectId):
            return value
        try:
            return ObjectId(value)
        except Exception:
            raise ValueError(f"Invalid ObjectId: {value}")

    class Config(ModelConfig):
        json_encoders = {
            ObjectId: str
        }

agent = ServiceAgent(
    _id="64e1c8e1f9e8f8c9b1234567",
    name="John Doe",
    mobile="9876543210",
    type="General",
    service_location_id="64e1c8e1f9e8f8c9b7654321",
    password="password123",
    confirm_password="password123"
)

print(agent.json())