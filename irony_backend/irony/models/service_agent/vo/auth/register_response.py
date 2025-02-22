from irony.models.common_response import CommonReponse
from irony.models.service_agent.service_agent import ServiceAgent
from pydantic import BaseModel


class AgentRegisterData(BaseModel):
    user: ServiceAgent


class AgentRegisterResponse(CommonReponse):
    data: AgentRegisterData
