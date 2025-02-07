from datetime import datetime
import pprint
import copy
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
from irony.models.update_pickup_pending_vo import UpdateOrderRequest
from irony.models.update_pickup_pending_vo import UpdateOrderResponse, UpdateOrderResponseBody
from irony.models.user import User
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger

order_simple_id_list =["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

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
        simple_ids: List[str] = []
        price = 0.0
        if request.items is not None:
            for item in request.items:
                if item is not None and item.price is not None:
                    price = price + item.price
        if request.total_price != price:
            response.error = "Price mismatch"
            response.success = False
            return response.model_dump()


        
        if request.current_status is not None and request.new_status is not None:
            if order.order_status is not None and len(order.order_status) >0  and request.current_status == OrderStatusEnum.PICKUP_PENDING and  OrderStatusEnum.PICKUP_PENDING == order.order_status.__getitem__(0).status:
                order.order_status.insert(0,(OrderStatus(status=OrderStatusEnum(request.new_status), created_on=now, updated_on=now)))
                order.updated_on =  now
                order.pickup_agent_id = request.pickup_by
                order.preferred_delivery_slot = request.preferred_delivey_slot
                order.picked_up_time = now
                if request.items is not None and len(request.items) > 0:
                    order_list = []
                    order_id_list = []
                    sub_id_list = []
                    for item in request.items:
                        order_list.append(copy.deepcopy(order))
                    map_oder_copies(order_list, request.items)
                    for index ,orderObj in enumerate(order_list):
                        # if orderObj.simple_id is not None:
                        #     orderObj.simple_id = orderObj.simple_id + "-" + order_simple_id_list[index]
                        #     simple_ids.append(orderObj.simple_id)
                        if orderObj.order_item and isinstance(orderObj.order_item.service_name, str):
                            orderObj.sub_id = orderObj.order_item.service_name[:2]
                            sub_id_list.append(orderObj.sub_id)
                        else:
                            orderObj.sub_id = None
                        if index == 0:
                            await db.order.replace_one({"_id": ObjectId(request.order_id)}, orderObj.model_dump(serialize_as_any = True))
                            order_id_list.append(str(request.order_id))
                        else:
                            result =await db.order.insert_one(orderObj.model_dump(serialize_as_any = True))
                            order_id_list.append(str(result.inserted_id))


                response.body= map_order_to_response(order, simple_ids , sub_id_list, order_id_list)
                response.success = True
        return response.model_dump()

    except Exception as e:
        logger.error(f"Error occured in update order : {e}")
        response.error = "Error occured in update order"    
        response.success = False
        return response.model_dump()

def map_oder_copies(order_list, items):
    for i in range(len(order_list)):
        if i!=0:
            order_list[i].id = ObjectId()
        order_list[i].order_item = items[i]

def map_order_to_response(order , simple_ids , sub_ids, order_ids):
    try:
        responseBody = UpdateOrderResponseBody()
        responseBody.parent_order_id = str(order.id)
        responseBody.sub_ids = sub_ids
        responseBody.order_ids = order_ids
        if order.location is not None:
            if order.location.nickname is not None :
                responseBody.location = order.location.nickname
            if order.location.location is not None:
                if order.location.location.coordinates is not None and len(order.location.location.coordinates) > 1:
                    responseBody.location = str(order.location.location.coordinates[0]) + "," + str(order.location.location.coordinates[1])
        
        if order.order_status is not None and len(order.order_status) > 0:
            responseBody.status = order.order_status[0].status

        return responseBody
    
    except Exception as e:
        logger.error(f"Error occured in fetch order details : {e}")
        return None