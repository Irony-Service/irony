from irony.config import config
from irony.models.message import MessageType, ReplyMessage


class WhatsappException(Exception):

    def __init__(
        self,
        message,
        reply_message_type: MessageType = MessageType.TEXT,
        reply_message=config.DEFAULT_ERROR_REPLY_MESSAGE,
        error_code=config.ERROR_CODES["INVALID_REQUEST"],
    ):
        super().__init__(message)
        self.message = message
        self.reply_message_type = reply_message_type
        self.reply_message = reply_message
        self.error_code = error_code

    def __str__(self):
        base_message = f"WhatsappException: {self.message}"
        if self.reply_message_type:
            base_message += f" | Reply Type: {self.reply_message_type}"
        if self.reply_message:
            base_message += f" | Reply: {self.reply_message}"
        if self.error_code:
            base_message += f" | Error Code: {self.error_code}"
        return base_message
