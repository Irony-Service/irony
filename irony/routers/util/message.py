import json
import requests

from app import config


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
        # self.message = {
        #     "messaging_product": "whatsapp",
        #     "recipient_type": "individual",
        #     "to": "<WHATSAPP_USER_PHONE_NUMBER>",
        #     "type": f"{type}",
        #     f"{type}": self.body,
        # }

    def send_message(self, to=None):
        # Implement your send_message logic here
        # Use the method name to make the HTTP request dynamically
        if to is not None:
            self.body["to"] = to

        if self.body["to"] == None:
            raise Exception(f"Please specify receipient(to) of message.")

        response = self._methods[self.method](
            self.url, headers=self.headers, data=json.dumps(self.body)
        )

        return response

        # Check the response
        # if response.status_code == 200:
        #     print('Request was successful')
        #     print('Response:', response.json())
        # else:
        #     print(f'Request failed with status code {response.status_code}')
