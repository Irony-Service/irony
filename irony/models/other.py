from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class MessagesFixed:
    id: ObjectId
    message_key: str
    type: str
    message: str


class messageType(str, Enum):
    STATIC = "STATIC"
    DYNAMIC = "DYNAMIC"


class Audit:
    table: str
    column: str
    old_value: str
    new_value: str
    created_on: datetime
