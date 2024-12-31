import pprint
from typing import Dict, List
from bson import ObjectId
from fastapi import Response

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.config import config
from irony.models.order import Order
from irony.models.order_status import OrderStatusEnum
from irony.models.fetch_orders_vo import (
    FetchOrderRequest,
    FetchOrderResponseBody,
    FetchOrdersResponse,
    OrderChunk,
)
from irony.models.service_agent import ServiceAgent
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger


async def fetch_orders(request: str):
    response = FetchOrdersResponse()
    try:
        agent_data = await db.service_agent.find_one({"mobile": request})
        if agent_data is None:
            raise Exception("Service agent not found")

        agent: ServiceAgent = ServiceAgent(**agent_data)

        if agent.service_location_ids is None:
            raise Exception("Service agent has no service locations")

        pipeline = [
            {
                "$match": {
                    "order_status.0.status": {
                        "$in": [
                            OrderStatusEnum.PICKUP_PENDING.value,
                            OrderStatusEnum.WORK_IN_PROGRESS.value,
                            OrderStatusEnum.DELIVERY_PENDING.value,
                        ]
                    },
                    "service_location_id": {"$in": agent.service_location_ids},
                }
            }
        ]
        orders: List[Order] = await db.order.aggregate(pipeline).to_list(None)

        if not orders:
            response.success = False
            response.error = "No orders found"
            return response.model_dump()

        response.body = setResponseBody(orders)
        response.success = True
        return response.model_dump()
    except Exception as e:
        logger.error(f"Error occured in fetch orders : {e}")
        response.success = False
        response.error = "Error occured in fetch orders"
        return response.model_dump()


def setResponseBody(orders):
    responseBody: Dict[str, List[OrderChunk]] = {
        "pending_pick_up": [],
        "work_in_progress": [],
        "delivery_pending": [],
    }
    for order in orders:
        order = Order(**order)
        if order.order_status[0].status == OrderStatusEnum.PICKUP_PENDING.value:
            orderChunk = setModel(order)
            responseBody.pending_pick_up.append(orderChunk)
        elif order.order_status[0].status == OrderStatusEnum.WORK_IN_PROGRESS.value:
            orderChunk = setModel(order)
            responseBody.work_in_progress.append(orderChunk)
        else:
            orderChunk = setModel(order)
            responseBody.delivery_pending.append(orderChunk)
    return responseBody


def setModel(order: Order):
    orderChunk = OrderChunk()
    if order is not None:
        orderChunk.order_id = str(order.id) if order.id is not None else None
        orderChunk.simple_id = order.simple_id
        orderChunk.clothes_count = str(order.count_range)
        if order.services is not None and len(order.services) > 0:
            orderChunk.service_name = order.services.__getitem__(0).service_name
        if order.pick_up_time is not None and order.pick_up_time.start is not None:
            orderChunk.pickup_time = order.pick_up_time.start.isoformat()
    return orderChunk
