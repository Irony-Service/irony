import pprint
from typing import List
from irony.models.pyobjectid import PyObjectId

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.whatsapp.contact_details import ContactDetails
from irony.config import config
from irony.models.service_agent.vo.fetch_order_details_vo import (
    FetchOrderDetailsRequest,
    FetchOrderDetailsResponse,
    FetchOrderDetailsResponsebody,
)
from irony.models.order import Order
from irony.models.order_status import OrderStatusEnum

from irony.models.service_location import ServiceLocation
from irony.models.user import User
from irony.config.logger import logger


async def fetch_order_details(request: FetchOrderDetailsRequest):
    try:
        order_data = await db.order.find_one({"_id": PyObjectId(request.order_id)})
        if order_data is None:
            raise WhatsappException("Order not found")
        order: Order = Order(**order_data)
        user_data = await db.user.find_one({"wa_id": order.user_wa_id})
        service_loc = await db.service_locations.find_one(
            {"_id": order.service_location_id}
        )
        response = FetchOrderDetailsResponse()
        if None is not service_loc:
            response.body = map_order_to_response(
                order, user_data, ServiceLocation(**service_loc)
            )
            response.success = True
        else:
            response.body = None
            response.error = "Service Location not found"
            response.success = False
        return response.model_dump()

    except Exception as e:
        logger.error(f"Error occured in fetch order details : {e}")
        response = FetchOrderDetailsResponse()
        response.body = None
        response.error = "Error occured in fetch order details"
        response.success = False
        return response.model_dump()


def map_order_to_response(order: Order, user, service_location: ServiceLocation):
    responsebody = FetchOrderDetailsResponsebody()
    responsebody.order_id = str(order.id)
    responsebody.simple_id = order.simple_id
    responsebody.count_range = order.count_range
    responsebody.services = order.services
    responsebody.service_location_id = str(order.service_location_id)
    if order.location is not None:
        responsebody.location = order.location.nickname
        if order.location.nickname is None or order.location.nickname == "":
            if order.location.location is not None:
                responsebody.location = (
                    str(order.location.location.coordinates[0])
                    + ","
                    + str(order.location.location.coordinates[1])
                )
    if order.pickup_date_time is not None:
        if order.pickup_date_time.start is not None:
            responsebody.pickup_time_start = order.pickup_date_time.start.isoformat()
        if order.pickup_date_time.end is not None:
            responsebody.pickup_time_end = order.pickup_date_time.end.isoformat()
    responsebody.time_slot = order.time_slot
    if order.order_status is not None and len(order.order_status) > 0:
        responsebody.status = order.order_status[0].status
    if user is not None:
        user = User(**user)
        responsebody.name = user.name
        responsebody.phone_number = user.wa_id

    return responsebody
