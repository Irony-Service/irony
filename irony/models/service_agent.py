from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, Union
from bson import ObjectId

# from irony.models.common_model import ModelConfig

class ModelConfig:
    arbitrary_types_allowed = True

class ServiceAgent(BaseModel):
    id: Optional[ObjectId] = Field(None, alias='_id')
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_id: Optional[ObjectId] = None
    password: Optional[str] = None

    @field_serializer("id", "service_location_id")
    def serialize_id(self, value: ObjectId) -> str:
        return str(value)

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

class ServiceAgentRegister(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_id: Optional[str] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None