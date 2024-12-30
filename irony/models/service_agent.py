from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import List, Optional, Union
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
    service_location_ids: Optional[List[ObjectId]] = None
    password: Optional[str] = None

    @field_serializer("id")
    def serialize_id(self, value: ObjectId) -> str:
        return str(value)
    
    @field_serializer("service_location_ids")
    def serialize_service_location_ids(self, values: List[ObjectId]) -> List[str]:
        if not values:
            return []
        return [str(value) for value in values]

    @field_validator("id", mode="before")
    def validate_and_convert_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = ObjectId(v)
            except Exception:
                raise ValueError(f"Invalid ObjectId string for id: {v}")
        elif not isinstance(v, ObjectId):
            raise ValueError(f"Invalid ObjectId for id: {v}")
        return v

    @field_validator("service_location_ids", mode="before")
    def validate_and_convert_service_location_ids(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            validated_list = []
            for item in v:
                if isinstance(item, str):
                    try:
                        item = ObjectId(item)
                    except Exception:
                        raise ValueError(f"Invalid ObjectId string in service_location_ids: {item}")
                elif not isinstance(item, ObjectId):
                    raise ValueError(f"Invalid ObjectId in service_location_ids: {item}")
                validated_list.append(item)
            return validated_list
        raise ValueError("service_location_ids must be a list of ObjectId or string.")

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