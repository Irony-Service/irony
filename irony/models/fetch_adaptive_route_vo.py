from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import ModelConfig

class FetchAdaptiveRouteRequest(BaseModel):
    service_agent_id:  Optional[str] = None;

    class Config(ModelConfig):
        pass

class FetchAdaptiveRouteResponseBody(BaseModel):
    mapLink: Optional[str] = None;

    class Config(ModelConfig):
        pass


class FetchAdaptiveRouteResponse(BaseModel):
    body: Optional[FetchAdaptiveRouteResponseBody] = None; # type: ignore
    success: Optional[bool] = None;
    error: Optional[str] = None;

    class Config(ModelConfig):
        pass