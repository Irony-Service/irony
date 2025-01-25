from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, field_serializer, field_validator

from irony.models.service_agent.service_agent import ServiceAgent

class ServiceAgentVo(ServiceAgent):
    @field_serializer("service_location_ids")
    def serialize_service_location_ids(self, values: List[ObjectId]) -> List[str]:
        if not values:
            return []
        return [str(value) for value in values]

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
                        raise ValueError(
                            f"Invalid ObjectId string in service_location_ids: {item}"
                        )
                elif not isinstance(item, ObjectId):
                    raise ValueError(
                        f"Invalid ObjectId in service_location_ids: {item}"
                    )
                validated_list.append(item)
            return validated_list
        raise ValueError("service_location_ids must be a list of ObjectId or string.")