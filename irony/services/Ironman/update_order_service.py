from datetime import datetime
import pprint
from typing import List
from bson import ObjectId
from fastapi import Response

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.config import config
from irony.models.fetch_order_details_vo import FetchOrderDetailsResponse
from irony.models.order import Order
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.fetch_orders_vo import FetchOrdersResponse, OrderChunk
from irony.models.update_order_vo import UpdateOrderRequest
from irony.models.update_order_vo import UpdateOrderResponse, UpdateOrderResponseBody
from irony.models.user import User
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger

async def update_order(request: UpdateOrderRequest):
    try:
        response = UpdateOrderResponse()
        now = datetime.now()
        order_data = await db.order.find_one({"_id": ObjectId(request.order_id)})
        if order_data is None:
            logger.error(f"Order not found for order_id : {request.order_id}")
            response.error = "Order not found"
            response.success = False
            return response.model_dump()
        order = Order(**order_data)
        
        if request.current_status is not None and request.new_status is not None:
            if order.order_status is not None and len(order.order_status) >0  and request.current_status == order.order_status.__getitem__(0).status:
                order.order_status.insert(0,(OrderStatus(status=OrderStatusEnum(request.new_status), created_on=now, updated_on=now)))
                order.updated_on =  now
                order.collected_cloths = int(request.collected_cloths) if request.collected_cloths is not None else None
                await db.order.replace_one({"_id": ObjectId(request.order_id)}, order.model_dump())
                response.body= map_order_to_response(order)
                response.success = True
        return response.model_dump()

    except Exception as e:
        logger.error(f"Error occured in update order : {e}")
        response.error = "Error occured in update order"    
        response.success = False
        return response.model_dump()

    
def map_order_to_response(order):
    try:
        responseBody = UpdateOrderResponseBody()
        responseBody.order_id = str(order.id)
        responseBody.simple_id = order.simple_id
        responseBody.count_range = order.count_range

        if order.location is not None:
            responseBody.location = order.location.nickname
            if order.location.nickname is  None or order.location.nickname == "":
                if order.location.location is not None:
                    responseBody.location = str(order.location.location.coordinates[0]) + "," + str(order.location.location.coordinates[1])

        if order.services is not None and len(order.services) > 0:
            responseBody.service_name = order.services[0].service_name
        if order.pick_up_time is not None:
            if order.pick_up_time.start is not None:
                responseBody.pickup_time_start = order.pick_up_time.start.isoformat()
            if order.pick_up_time.end is not None:
                responseBody.pickup_time_end = order.pick_up_time.end.isoformat()
        responseBody.time_slot = order.time_slot
        if order.order_status is not None and len(order.order_status) > 0:
            responseBody.status = order.order_status[0].status

        return responseBody
    
    except Exception as e:
        logger.error(f"Error occured in fetch order details : {e}")
        return None