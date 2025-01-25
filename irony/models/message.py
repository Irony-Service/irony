from enum import Enum
from typing import Any, List, Optional
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config


class MessageType(str, Enum):
    TEXT = "TEXT"
    INTERACTIVE = "INTERACTIVE"


class ReplyMessage(BaseModel):
    type: MessageType = MessageType.TEXT
    content: Any

    model_config = shared_config


class MessageConfig(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    message_key: Optional[str] = None
    type: Optional[str] = None
    message_options: Optional[List[str]] = None
    call_to_action: Optional[List[str]] = None
    message: Optional[Any] = None

    model_config = shared_config
