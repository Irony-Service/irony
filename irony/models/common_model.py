from typing import ClassVar, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


class ModelConfig:
    arbitrary_types_allowed = True


shared_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str})


class CommonModel(BaseModel):

    @field_validator(
        "id",
        "order_id",
        "service_location_id",
        "user_id",
        "service_id",
        mode="before",
        check_fields=False,
    )
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

    @field_serializer(*OBJECT_ID_FIELDS, when_used="unless-none", check_fields=False)
    def serialize_id(self, value: Optional[ObjectId]) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, ObjectId):
            raise TypeError(f"Expected ObjectId, got {type(value)}")
        return str(value)


class ModelConfig:
    arbitrary_types_allowed = True
