from ast import Dict
from bson import ObjectId
from typing import Any


class PyObjectIdOld(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: Dict[str, Any]) -> Dict[str, Any]:
        schema.update(type="string")
        return schema
