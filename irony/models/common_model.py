from typing import ClassVar
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


class ModelConfig:
    arbitrary_types_allowed = True


shared_config = ConfigDict(arbitrary_types_allowed=True, json_encoders = {ObjectId: str})


class CommonModel(BaseModel):
    # Annotate as ClassVar to avoid Pydantic treating it as a field
    OBJECT_ID_FIELDS: ClassVar[tuple[str, ...]] = (
        "id",
        "order_id",
        "service_location_id",
        "user_id",
        "service_id",
    )

    @field_validator(*OBJECT_ID_FIELDS, mode="before", check_fields=False)
    def validate_and_convert_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = ObjectId(v)
            except Exception:
                raise ValueError(f"Invalid ObjectId string for field value: {v}")
        elif not isinstance(v, ObjectId):
            raise TypeError(f"Expected ObjectId, got {type(v)} for field value: {v}")
        return v

    @field_serializer(*OBJECT_ID_FIELDS, when_used="unless-none", check_fields=False)
    def serialize_id(self, value: ObjectId | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, ObjectId):
            raise TypeError(f"Expected ObjectId, got {type(value)}")
        return str(value)

    model_config = shared_config
