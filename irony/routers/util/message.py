import json
import requests

from irony import config


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
        self.body = json.dumps(body)

    def send_message(self):
        # Implement your send_message logic here
        # Use the method name to make the HTTP request dynamically
        response = self._methods[self.method](
            self.url, headers=self.headers, data=self.body
        )

        return response

        # Check the response
        # if response.status_code == 200:
        #     print('Request was successful')
        #     print('Response:', response.json())
        # else:
        #     print(f'Request failed with status code {response.status_code}')
