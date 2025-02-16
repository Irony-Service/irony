from typing import List
from fastapi import Response, HTTPException

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.whatsapp.contact_details import ContactDetails
from irony.config import config
from irony.models.service_agent.vo.fetch_adaptive_route_vo import (
    FetchAdaptiveRouteRequest,
    FetchAdaptiveRouteResponse,
)



from irony.config.logger import logger


async def fetch_route(request: FetchAdaptiveRouteRequest):
    try:
        response = FetchAdaptiveRouteResponse()
        response.success = True
        return response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch_route: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching adaptive route")
