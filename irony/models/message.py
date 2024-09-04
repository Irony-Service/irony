from enum import Enum
from typing import Any, List
from bson import ObjectId
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class MessageType(str, Enum):
    TEXT = "TEXT"
    INTERACTIVE = "INTERACTIVE"


class ReplyMessage(BaseModel):
    type: MessageType = MessageType.TEXT
    content: Any

    class Config(ModelConfig):
        pass


class MessageConfig(BaseModel):
    _id: ObjectId = None
    message_key: str = None
    type: str = None
    message_options: List[str] = None
    call_to_action: List[str] = None
    message: Any = None
