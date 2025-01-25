from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from typing import List, Optional, Union
from bson import ObjectId
from irony.models.common_model import shared_config
from irony.models.pyobjectid import PyObjectId


# from irony.models.common_model import shared_config


class ModelConfig:
    arbitrary_types_allowed = True


class ServiceAgent(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_ids: Optional[List[PyObjectId]] = None
    password: Optional[str] = Field(None, exclude=True)

    model_config = shared_config

    # class Config(ModelConfig):
    #     json_encoders = {ObjectId: str}
    #     pass


class ServiceAgentRegister(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    service_location_ids: Optional[List[str]] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None
