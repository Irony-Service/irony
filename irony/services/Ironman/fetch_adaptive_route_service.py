from typing import List
from fastapi import Response

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

    except Exception as e:
        logger.error(f"Error occured in fetch adaptive route : {e}")
        response = FetchAdaptiveRouteResponse()
        response.body = None
        response.error = "Error occured in fetch adaptive route service"
        response.success = False
        return response.model_dump()
