from datetime import datetime
import pprint
import copy
from typing import Dict, List, Optional, Union
from irony.models.pyobjectid import PyObjectId
from fastapi import Response, HTTPException
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


async def update_order(request: UpdateOrderRequest):
    try:
        response = UpdateOrderResponse()
        now = datetime.now()
        order_data = await db.order.find_one({"_id": PyObjectId(request.order_id)})
        if order_data is None:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = Order(**order_data)

        if request.current_status and request.new_status:
            if not order.order_status or len(order.order_status) == 0:
                raise HTTPException(status_code=400, detail="Order status not found")

            validate_request_status(request)

            order_status = order.order_status[0].status

            # if order_status != OrderStatusEnum(request.current_status):
            #     response.message = (
            #         "Status for this order has changed. Please refresh the page."
            #     )
            #     response.success = False
            #     return response.model_dump()
            # Execute bulk operations outside the loop
            bulk_operations: List[ReplaceOne | InsertOne] = []
            if order_status == OrderStatusEnum.PICKUP_PENDING:
                await process_pending_pickup_order_update(request, response, now, order, bulk_operations)
            
            if order_status == OrderStatusEnum.WORK_IN_PROGRESS:
                if request.new_status == OrderStatusEnum.DELIVERY_PENDING:
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
                    bulk_operations.append(
                        ReplaceOne(
                            {"_id": PyObjectId(request.order_id)},
                            order.model_dump(exclude_unset=True, by_alias=True),
                        )
                    )
                    await bulk_write_operations("order", bulk_operations)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while updating order")

async def process_pending_pickup_order_update(request: UpdateOrderRequest, response: UpdateOrderResponse, now:datetime, order: Order, bulk_operations:List[ReplaceOne | InsertOne] ):
    if request.new_status == OrderStatusEnum.WORK_IN_PROGRESS:
        sevice_grouped_items: Dict[str, List[OrderItem]] = {}

        await validate_price(request, sevice_grouped_items)

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

        await update_location_if_nickname_added(order, request.location_nickname)

        if request.items:
            order_list: List[Order] = []
            order_id_list = []
            sub_id_dict = {}

            for index, entry in enumerate(sevice_grouped_items.items()):
                order_instance = order
                if index != 0:
                    order_instance = copy.deepcopy(order)
                    order_instance.id = PyObjectId()
                                # order_instance.order_items = None

                order_instance.order_items = entry[1]
                order_instance.sub_id = str(entry[0])[:2]
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
                                        {"_id": PyObjectId(request.order_id)}, order_dict
                                    )
                                )
                else:
                                # Insert new documents for subsequent items
                    bulk_operations.append(InsertOne(order_dict))

                order_id_list.append(str(order_instance.id))
                order_list.append(order_instance)

                        # Execute all operations in a transaction
            await bulk_write_operations("order", bulk_operations)

                        # Update order_id_list with newly inserted IDs if any
                        # if result.get("upserted_ids"):
                        #     for idx, inserted_id in result["upserted_ids"].items():
                        #         order_id_list[int(idx)] = str(inserted_id)

            response.data = UpdateOrderResponseBody(sub_id_dict=sub_id_dict, order_ids=order_id_list)
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
        bulk_operations.append(
                        ReplaceOne(
                            {"_id": PyObjectId(request.order_id)},
                            order.model_dump(exclude_unset=True, by_alias=True),
                        )
                    )
        await bulk_write_operations("order", bulk_operations)

async def validate_price(request: UpdateOrderRequest, sevice_grouped_items):
    if request.items:
        price = 0.0
        price_ids = [PyObjectId(item.price_id) for item in request.items]
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
                    raise HTTPException(
                                            status_code=400, 
                                            detail=f"Price mismatch for item: {item.price_id}"
                                        )
                price = price + item.amount
        if request.total_price != price:
            raise HTTPException(status_code=400, detail="Price mismatch")
        
async def update_location_if_nickname_added(order: Order, location_nickname: Optional[str]):
            if location_nickname and order.location:
                order.location.nickname = location_nickname
                # Update nickname for existing location document
                await db.location.update_one(
                    {"_id": order.location.id},
                    {"$set": {"nickname": location_nickname}}
                )
                # check if need to udpate location in user

def validate_request_status(request):
    if (
                request.current_status not in OrderStatusEnum.__members__.values()
                or request.new_status not in OrderStatusEnum.__members__.values()
            ):
        raise HTTPException(status_code=400, detail="Invalid status provided")
            
    if(request.current_status == request.new_status):
        raise HTTPException(status_code=400, detail="Current status and new status are same")

