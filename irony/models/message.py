from enum import Enum
from pydantic import BaseModel

from irony.models.common_model import ModelConfig


class MessageType(str, Enum):
    TEXT = "TEXT"
    INTERACTIVE = "INTERACTIVE"


class ReplyMessage(BaseModel):
    type: MessageType = MessageType.TEXT
    content: any

    class Config(ModelConfig):
        pass
