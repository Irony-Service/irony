from datetime import datetime
from enum import Enum
from irony.models.pyobjectid import PyObjectId


class MessagesFixed:
    id: PyObjectId
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
