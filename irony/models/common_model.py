from bson import ObjectId
from pydantic import BaseModel, field_serializer, field_validator


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

    # Common serializer for age
    @field_serializer(
        "id",
        "order_id",
        "service_location_id",
        "user_id",
        "service_id",
        check_fields=False,
    )
    def serialize_id(self, value: ObjectId) -> str:
        return str(value)


class ModelConfig:
    arbitrary_types_allowed = True
