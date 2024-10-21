from enum import Enum
from typing import Any, List, Optional
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
    _id: Optional[ObjectId] = None
    message_key: Optional[str] = None
    type: Optional[str] = None
    message_options: Optional[List[str]] = None
    call_to_action: Optional[List[str]] = None
    message: Optional[Any] = None
