from irony.models.common_response import CommonReponse
from irony.models.service_agent.service_agent import ServiceAgent
from pydantic import BaseModel

class LoginUserData(BaseModel):
    access_token: str
    token_type: str
    user: ServiceAgent

class LoginUserResponse(CommonReponse):
    data: LoginUserData