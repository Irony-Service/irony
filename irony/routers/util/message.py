import requests

from irony import config;


class Message:
    _methods = {
    'GET': requests.get,
    'POST': requests.post,
    'PUT': requests.put,
    'DELETE': requests.delete,
    # Add more methods as needed
    }
    def __init__(self, url, method='POST', headers=None, body=None):
        if(headers is None):
            bearer_token = config.WHATSAPP_CONFIG['bearer_token'];
            headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}
        if method not in self._methods:
            raise Exception(f"Invalid method while creating method object. Please choose from {self._methods.keys()}")
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body

    def send_message(self):
        # Implement your send_message logic here
            # Use the method name to make the HTTP request dynamically
            response = self._methods[self.method](self.url, headers=self.headers, data=self.body)
            
            return response;

            # Check the response
            # if response.status_code == 200:
            #     print('Request was successful')
            #     print('Response:', response.json())
            # else:
            #     print(f'Request failed with status code {response.status_code}')