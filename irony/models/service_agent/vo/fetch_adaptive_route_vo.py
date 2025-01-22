from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from irony.models.common_model import shared_config


class FetchAdaptiveRouteRequest(BaseModel):
    service_agent_id: Optional[str] = None

    model_config = shared_config


class FetchAdaptiveRouteResponseBody(BaseModel):
    mapLink: Optional[str] = None

    model_config = shared_config


class FetchAdaptiveRouteResponse(BaseModel):
    body: Optional[FetchAdaptiveRouteResponseBody] = None
    # type: ignore
    success: Optional[bool] = None
    error: Optional[str] = None

    model_config = shared_config
