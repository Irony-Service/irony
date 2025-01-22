from datetime import datetime
import pprint
import copy
from typing import Dict, List, Union
from bson import ObjectId
from fastapi import Response
from pymongo import InsertOne, ReplaceOne

from irony.db import bulk_write_operations, db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.service import Service
from irony.models.order_item import OrderItem
from irony.models.prices import Prices
from irony.models.whatsapp.contact_details import ContactDetails
from irony.config import config
from irony.models.service_agent.vo.fetch_order_details_vo import (
    FetchOrderDetailsResponse,
)
from irony.models.order import Order
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.service_agent.vo.fetch_orders_vo import (
    FetchOrdersResponse,
    OrderChunk,
)
from irony.models.service_agent.vo.update_pickup_pending_vo import UpdateOrderRequest
from irony.models.service_agent.vo.update_pickup_pending_vo import (
    UpdateOrderResponse,
    UpdateOrderResponseBody,
)
from irony.models.user import User
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger

order_simple_id_list = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]


async def update_order(request: UpdateOrderRequest):
    try:
        response = UpdateOrderResponse()
        now = datetime.now()
        order_data = await db.order.find_one({"_id": ObjectId(request.order_id)})
        if order_data is None:
            logger.error(f"Order not found for order_id : {request.order_id}")
            response.message = "Order not found"
            response.success = False
            return response.model_dump()
        order = Order(**order_data)
        simple_ids: List[str] = []

        if request.current_status and request.new_status:
            if not order.order_status or len(order.order_status) == 0:
                response.message = "Order status not found"
                response.success = False
                return response.model_dump()

            if (
                request.current_status not in OrderStatusEnum.__members__.values()
                or request.new_status not in OrderStatusEnum.__members__.values()
            ):
                response.message = "Invalid status provided"
                response.success = False
                return response.model_dump()

            order_status = order.order_status[0].status

            # if order_status != OrderStatusEnum(request.current_status):
            #     response.message = (
            #         "Status for this order has changed. Please refresh the page."
            #     )
            #     response.success = False
            #     return response.model_dump()

            if order_status == OrderStatusEnum.PICKUP_PENDING:
                if request.new_status == OrderStatusEnum.WORK_IN_PROGRESS:
                    sevice_grouped_items: Dict[str, List[OrderItem]] = {}

                    if request.items:
                        price = 0.0
                        price_ids = [ObjectId(item.price_id) for item in request.items]
                        prices = await db.prices.find(
                            {"_id": {"$in": price_ids}}
                        ).to_list(None)
                        prices = [Prices(**price) for price in prices]
                        price_map = {str(price.id): price for price in prices}

                        for item in request.items:
                            associated_service_id = price_map[item.price_id].service_id
                            if associated_service_id not in sevice_grouped_items:
                                sevice_grouped_items[associated_service_id] = []

                            sevice_grouped_items[associated_service_id].append(item)

                            if item and item.amount:
                                if (item.amount / item.count) != price_map[
                                    item.price_id
                                ].price:
                                    response.message = (
                                        "Price mismatch for item : " + item.price_id
                                    )
                                    response.success = False
                                    return response.model_dump()
                                price = price + item.amount
                        if request.total_price != price:
                            response.message = "Price mismatch"
                            response.success = False
                            return response.model_dump()

                    order.order_status.insert(
                        0,
                        (
                            OrderStatus(
                                status=OrderStatusEnum(request.new_status),
                                created_on=now,
                                updated_on=now,
                            )
                        ),
                    )
                    order.updated_on = now
                    # TODO change this to user who made this request.
                    order.pickup_agent_id = request.pickup_by
                    order.picked_up_time = now

                    if request.items:
                        order_list: List[Order] = []
                        order_id_list = []
                        sub_id_list = []
                        sub_id_dict = {}

                        # Execute bulk operations outside the loop
                        bulk_operations: List[ReplaceOne | InsertOne] = []

                        for index, entry in enumerate(sevice_grouped_items.items()):
                            order_instance = order
                            if index != 0:
                                order_instance = copy.deepcopy(order)
                                order_instance.id = ObjectId()
                                # order_instance.order_items = None

                            order_instance.order_items = entry[1]
                            order_instance.sub_id = str(entry[0])[:2]
                            sub_id_list.append(order_instance.sub_id)
                            service: Service = config.DB_CACHE["id_to_service_map"][
                                entry[0]
                            ]

                            sub_id_dict[service.service_name] = order_instance.sub_id

                            # Build list for bulk operations
                            order_dict = order_instance.model_dump(
                                exclude_unset=True,
                                by_alias=True,
                                exclude={"id"},
                            )

                            if index == 0:
                                # Replace the first document
                                bulk_operations.append(
                                    ReplaceOne(
                                        {"_id": ObjectId(request.order_id)}, order_dict
                                    )
                                )
                            else:
                                # Insert new documents for subsequent items
                                bulk_operations.append(InsertOne(order_dict))

                            order_id_list.append(str(order_instance.id))
                            order_list.append(order_instance)

                        # Execute all operations in a transaction
                        result = await bulk_write_operations("order", bulk_operations)

                        # Update order_id_list with newly inserted IDs if any
                        # if result.get("upserted_ids"):
                        #     for idx, inserted_id in result["upserted_ids"].items():
                        #         order_id_list[int(idx)] = str(inserted_id)

                        response.body = map_order_to_response(
                            order, simple_ids, sub_id_list, sub_id_dict, order_id_list
                        )
                if (
                    request.new_status == OrderStatusEnum.PICKUP_USER_NO_RESP
                    or request.new_status == OrderStatusEnum.PICKUP_USER_REJECTED
                ):
                    order.order_status.insert(
                        0,
                        (
                            OrderStatus(
                                status=OrderStatusEnum(request.new_status),
                                created_on=now,
                                updated_on=now,
                            )
                        ),
                    )
                    order.updated_on = now
                    response.body = map_order_to_response(order, simple_ids, [], {}, [])
        response.success = True
        return response.model_dump()

    except Exception as e:
        logger.error(f"Error occured in update order : {e}", exc_info=True)
        response.message = "Error occured in update order"
        response.success = False
        return response.model_dump()


def map_oder_copies(order_list, items):
    for i in range(len(order_list)):
        if i != 0:
            order_list[i].id = ObjectId()
        order_list[i].order_item = items[i]


def map_order_to_response(order: Order, simple_ids, sub_ids, sub_id_dict, order_ids):
    try:
        responseBody = UpdateOrderResponseBody()
        responseBody.parent_order_id = str(order.id)
        responseBody.sub_ids = sub_ids
        responseBody.order_ids = order_ids
        responseBody.sub_id_dict = sub_id_dict
        if order.location is not None:
            if order.location.nickname is not None:
                responseBody.location = order.location.nickname
            if order.location.location is not None:
                if (
                    order.location.location.coordinates is not None
                    and len(order.location.location.coordinates) > 1
                ):
                    responseBody.location = (
                        str(order.location.location.coordinates[0])
                        + ","
                        + str(order.location.location.coordinates[1])
                    )

        if order.order_status is not None and len(order.order_status) > 0:
            responseBody.status = order.order_status[0].status

        return responseBody

    except Exception as e:
        logger.error(f"Error occured in fetch order details : {e}")
        return None
