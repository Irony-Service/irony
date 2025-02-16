from pydantic import BaseModel, Field


class AgentLoginRequest(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)
    password: str
