from irony.models.common_response import CommonReponse
from irony.models.service_agent.service_agent import ServiceAgent
from pydantic import BaseModel

class RegisterAgentData(BaseModel):
    user: ServiceAgent

class RegisterAgentResponse(CommonReponse):
    data: RegisterAgentData