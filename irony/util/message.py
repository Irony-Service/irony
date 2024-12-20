import json
import requests

from irony.config import config
from irony.config.logger import logger
from irony.db import db


class Message:
    _methods = {
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
        # Add more methods as needed
    }
    bearer_token = config.WHATSAPP_CONFIG["bearer_token"]
    default_headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }

    def __init__(
        self,
        body=None,
        # type="interactive",
        url: str = config.WHATSAPP_CONFIG["message_url"],
        method: str = "POST",
        headers=default_headers,
    ):
        if method not in self._methods:
            raise Exception(
                f"Invalid method while creating method object. Please choose from {self._methods.keys()}"
            )
        if not bool(body):
            raise Exception(f"Please provide message body")
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body

    def send_message(self, to=None):
        logger.info("Starting send_message ", to, self.body)
        # 1. Create request body for sending message.
        if to is not None:
            self.body["to"] = to

        if self.body["to"] == None:
            raise Exception(f"Please specify receipient(to) of message.")

        # 2. Send message to user.
        response = self._methods[self.method](
            self.url, headers=self.headers, data=json.dumps(self.body)
        )
        # Check the response
        # if response.status_code == 200:
        #     logger.info('Request was successful')
        #     logger.info('Response:', response.json())
        # else:
        #     logger.info(f'Request failed with status code {response.status_code}')
        return response

    async def send_message(self, to=None, last_message_update=None):
        # 1. Create request body for sending message.
        if to is not None:
            self.body["to"] = to

        if self.body["to"] == None:
            raise Exception(f"Please specify receipient(to) of message.")

        # 2. Send message to user.
        response = self._methods[self.method](
            self.url, headers=self.headers, data=json.dumps(self.body)
        )
        response_data = response.json()
        logger.info(f"Sent message response : {response_data}")

        # 3. Update last message for user.
        if last_message_update != None:
            last_message_update["user"] = to
            if "messages" in response_data and "id" in response_data["messages"][0]:
                last_message_update["last_sent_msg_id"] = response_data["messages"][0][
                    "id"
                ]
            result = await db.last_message.replace_one(
                {"user": to},
                last_message_update,
                # {"$set": last_message_update},
                upsert=True,
            )

            logger.info(
                f"Temp, last message doc replaced. update documents count: {result.modified_count}"
            )

        return response
