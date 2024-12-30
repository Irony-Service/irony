from typing import List
from bson import ObjectId
from fastapi import Response

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.config import config
from irony.models.fetch_adaptive_route_vo import FetchAdaptiveRouteRequest, FetchAdaptiveRouteResponse
from irony.models.fetch_order_details_vo import FetchOrderDetailsRequest, FetchOrderDetailsResponse, FetchOrderDetailsResponsebody
from irony.models.order import Order
from irony.models.order_status import OrderStatusEnum
from irony.models.fetch_orders_vo import FetchOrdersResponse, OrderChunk
from irony.models.user import User
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
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