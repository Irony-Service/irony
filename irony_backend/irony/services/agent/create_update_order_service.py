from ast import Set
from datetime import datetime
import pprint
import copy
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi.background import P
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.pickup_tIme import PickupDateTime
from irony.models.pyobjectid import PyObjectId
from fastapi import Response, HTTPException
from pymongo import DeleteOne, InsertOne, ReplaceOne

from irony.db import bulk_write_operations, db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.service import Service
from irony.models.order_item import OrderItem
from irony.models.prices import Prices
from irony.models.service_agent.vo.order_request_vo import (
    CommonOrderRequest,
    CommonOrderResponse,
    CommonOrderResponseBody,
)
from irony.models.whatsapp.contact_details import ContactDetails
from irony.config import config
from irony.models.service_agent.vo.fetch_order_details_vo import (
    FetchOrderDetailsResponse,
)
from irony.models.order import Order
from irony.models.order_status import OrderStatus
from irony.models.service_agent.vo.fetch_orders_response import (
    FetchOrdersResponse,
)
from irony.models.service_agent.vo.update_pickup_pending_vo import UpdateOrderRequest
from irony.models.service_agent.vo.update_pickup_pending_vo import (
    UpdateOrderResponse,
)
from irony.models.user import User
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger
from irony.models.service_agent.vo.create_order_vo import (
    CreateOrderRequest,
    CreateOrderResponse,
)


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
                await process_pending_pickup_order_update(
                    request, response, now, order, bulk_operations
                )

            if order_status == OrderStatusEnum.WORK_IN_PROGRESS:
                if request.new_status == OrderStatusEnum.DELIVERY_PENDING:
                    await update_order_status(request, now, order, bulk_operations)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid status transition from WORK_IN_PROGRESS",
                    )

            elif order_status == OrderStatusEnum.DELIVERY_PENDING:
                if request.new_status == OrderStatusEnum.DELIVERED:
                    await update_order_status(request, now, order, bulk_operations)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid status transition from DELIVERY_PENDING",
                    )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_order: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while updating order"
        )


async def update_order_status(request, now, order, bulk_operations):
    if order.order_status is None:
        order.order_status = []
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


def create_update_order_from_service_grouped_item(
    order: Order,
    sevice_grouped_item: Tuple[str, List[OrderItem]],
    is_new_instance: bool,
    is_new_id: bool,
) -> Order:
    order_instance = order
    if is_new_instance:
        order_instance = copy.deepcopy(order)
    if is_new_id:
        order_instance.id = PyObjectId()
        # order_instance.order_items = None

    order_instance.order_items = sevice_grouped_item[1]
    order_instance.sub_id = str(sevice_grouped_item[0])[:2]
    order_instance.total_count = sum(item.count for item in order_instance.order_items)
    order_instance.total_price = sum(item.amount for item in order_instance.order_items)

    return order_instance


async def process_pending_pickup_order_update(
    request: UpdateOrderRequest,
    response: UpdateOrderResponse,
    now: datetime,
    order: Order,
    bulk_operations: List[ReplaceOne | InsertOne | DeleteOne],
):
    if request.new_status == OrderStatusEnum.WORK_IN_PROGRESS:
        sevice_grouped_items: Dict[str, List[OrderItem]] = {}

        await validate_price(request, sevice_grouped_items)

        if order.order_status is None:
            order.order_status = []
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
            # If more than 1 service chooosed.
            if len(sevice_grouped_items.keys() > 1):
                # Create new order for each service
                for index, service_grouped_item in enumerate(
                    sevice_grouped_items.items()
                ):
                    # if index == 0:
                    #     order_instance = create_update_order_from_service_grouped_item(
                    #         order, service_grouped_item, False, False, sub_id_dict
                    #     )
                    #     order_dict = order_instance.model_dump(
                    #         exclude_unset=True,
                    #         by_alias=True,
                    #         exclude={"id"},
                    #     )
                    #     bulk_operations.append(
                    #         ReplaceOne({"_id": PyObjectId(request.order_id)}, order_dict)
                    #     )
                    # else:
                    order_instance: Order = (
                        create_update_order_from_service_grouped_item(
                            order, service_grouped_item, True, False
                        )
                    )
                    order_dict = order_instance.model_dump(
                        exclude_unset=True,
                        by_alias=True,
                        exclude={"id"},
                    )
                    bulk_operations.append(InsertOne(order_dict))

                    service: Service = config.DB_CACHE["id_to_service_map"][
                        service_grouped_item[0]
                    ]
                    sub_id_dict[service.service_name] = order_instance.sub_id
                    order_id_list.append(str(order_instance.id))
                    order_list.append(order_instance)

                # Delete original order from order collection
                bulk_operations.append(
                    DeleteOne(
                        {"_id": order.id},
                    )
                )
                # Execute all operations in a transaction
                await bulk_write_operations("order", bulk_operations)

                order.order_items = request.items
                order.child_order_ids = order_id_list
                await db.parent_order.insert_one(order.model_dump(exclude_unset=True))
            else:
                order.order_items = request.items
                order.total_price = request.total_price
                order.total_count = sum(item.count for item in request.items)

                result = db.order.replace_one(
                    {"_id": PyObjectId(request.order_id)},
                    order.model_dump(exclude_unset=True, by_alias=True),
                )
                order_id_list.append(str(result.inserted_id))
                order_list.append(order_instance)

            # Update order_id_list with newly inserted IDs if any
            # if result.get("upserted_ids"):
            #     for idx, inserted_id in result["upserted_ids"].items():
            #         order_id_list[int(idx)] = str(inserted_id)

            response.data = CommonOrderResponseBody(
                sub_id_dict=sub_id_dict, order_ids=order_id_list
            )
    if (
        request.new_status == OrderStatusEnum.PICKUP_USER_NO_RESP
        or request.new_status == OrderStatusEnum.PICKUP_USER_REJECTED
    ):
        if order.order_status is None:
            order.order_status = []
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


async def validate_price(
    request: CommonOrderRequest, sevice_grouped_items: Dict[str, List[OrderItem]]
):
    if request.items:
        price = 0.0
        price_ids = [PyObjectId(item.price_id) for item in request.items]
        prices = await db.prices.find({"_id": {"$in": price_ids}}).to_list(None)
        prices = [Prices(**price) for price in prices]
        price_map = {str(price.id): price for price in prices}

        for item in request.items:
            associated_service_id = price_map[item.price_id].service_id
            if associated_service_id not in sevice_grouped_items:
                sevice_grouped_items[associated_service_id] = []

            sevice_grouped_items[associated_service_id].append(item)

            if item and item.amount:
                if (item.amount / item.count) != price_map[item.price_id].price:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Price mismatch for item: {item.price_id}",
                    )
                price = price + item.amount
        if request.total_price != price:
            raise HTTPException(status_code=400, detail="Price mismatch")


async def update_location_if_nickname_added(
    order: Order, location_nickname: Optional[str]
):
    if location_nickname and order.location:
        order.location.nickname = location_nickname
        # Update nickname for existing location document
        await db.location.update_one(
            {"_id": order.location.id}, {"$set": {"nickname": location_nickname}}
        )
        # check if need to udpate location in user


def validate_request_status(request):
    if (
        request.current_status not in OrderStatusEnum.__members__.values()
        or request.new_status not in OrderStatusEnum.__members__.values()
    ):
        raise HTTPException(status_code=400, detail="Invalid status provided")

    if request.current_status == request.new_status:
        raise HTTPException(
            status_code=400, detail="Current status and new status are same"
        )


def set_timeslot_and_pickup() -> tuple[str, PickupDateTime]:
    time_slot_id = None
    pickup_datetime = datetime.now()
    current_time_str = pickup_datetime.strftime("%H:%M")

    ordered_time_slots = config.DB_CACHE["ordered_time_slots"]
    h, m, he, me = None, None, None, None
    if current_time_str < ordered_time_slots[0]["start_time"]:
        time_slot_id = ordered_time_slots[0]["key"]
        h, m = map(int, ordered_time_slots[0]["start_time"].split(":"))
        he, me = map(int, ordered_time_slots[0]["end_time"].split(":"))
    else:
        for i in ordered_time_slots:
            time_slot_id = ordered_time_slots[0]["key"]
            h, m = map(int, i["start_time"].split(":"))
            he, me = map(int, i["end_time"].split(":"))
            if i["start_time"] <= current_time_str <= i["end_time"]:
                break

    if h is None or m is None or he is None or me is None:
        raise HTTPException(
            status_code=500,
            detail="Unable to create order (pickup_datetime issue). Please try again later",
        )

    start_time = pickup_datetime.replace(hour=h, minute=m, second=0, microsecond=0)
    end_time = pickup_datetime.replace(hour=he, minute=me, second=0, microsecond=0)
    date_time = pickup_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    pickup_date_time = PickupDateTime(
        date=date_time,
        start=start_time,
        end=end_time,
    )

    if not time_slot_id:
        raise HTTPException(
            status_code=500,
            detail="Unable to create order (time_slot_id issue). Please try again later",
        )

    return time_slot_id, pickup_date_time


async def create_order(request: CreateOrderRequest):
    try:
        response = CommonOrderResponse()

        sevice_grouped_items: Dict[str, List[OrderItem]] = {}
        validate_price(request, sevice_grouped_items)

        now = datetime.now()

        # Check if user exists, create if not
        user_data = await db.user.find_one({"wa_id": request.user_wa_id})
        user_id: str | PyObjectId | None = None
        if not user_data:
            new_user = User(wa_id=request.user_wa_id, created_on=now)
            result = await db.user.insert_one(
                new_user.model_dump(exclude_unset=True, by_alias=True)
            )
            user_id = result.inserted_id
        else:
            user_id = User(**user_data).id

        time_slot_id, pickup_date_time = set_timeslot_and_pickup()

        # Create new order
        new_order = Order(
            user_id=PyObjectId(user_id),
            user_wa_id=request.user_wa_id,
            service_location_id=request.service_location_id,
            notes=request.notes,
            order_items=request.items,
            total_price=request.total_price,
            order_status=[
                OrderStatus(
                    status=OrderStatusEnum.WORK_IN_PROGRESS,
                    created_on=now,
                    updated_on=now,
                )
            ],
            time_slot=time_slot_id,
            pickup_date_time=pickup_date_time,
            created_on=now,
            is_active=True,
        )

        # Calculate total count
        total_count = sum(item.count for item in request.items)
        new_order.total_count = total_count

        bulk_operations: List[InsertOne] = []
        if request.items:
            order_list: List[Order] = []
            order_id_list = []
            sub_id_dict = {}
            if len(sevice_grouped_items.keys() > 1):
                for index, service_grouped_item in enumerate(
                    sevice_grouped_items.items()
                ):

                    order_instance = create_update_order_from_service_grouped_item(
                        new_order, service_grouped_item, True, False
                    )
                    order_dict = order_instance.model_dump(
                        exclude_unset=True,
                        by_alias=True,
                        exclude={"id"},
                    )
                    bulk_operations.append(InsertOne(order_dict))

                    service: Service = config.DB_CACHE["id_to_service_map"][
                        service_grouped_item[0]
                    ]
                    sub_id_dict[service.service_name] = order_instance.sub_id
                    order_id_list.append(str(order_instance.id))
                    order_list.append(order_instance)

                # Execute all operations in a transaction
                await bulk_write_operations("order", bulk_operations)

                new_order.child_order_ids = order_id_list
                result = await db.parent_order.insert_one(
                    new_order.model_dump(exclude_unset=True, by_alias=True)
                )
            else:
                result = db.order.insert_one(
                    new_order.model_dump(exclude_unset=True, by_alias=True)
                )
                order_id_list.append(str(result.inserted_id))
                order_list.append(new_order)

        response.data = CommonOrderResponseBody(
            sub_id_dict=sub_id_dict, order_ids=order_id_list
        )

        # # Set count range based on total count
        # if total_count <= 5:
        #     new_order.count_range = "1-5"
        #     new_order.count_range_description = "1-5"
        # elif total_count <= 10:
        #     new_order.count_range = "6-10"
        #     new_order.count_range_description = "6-10"
        # else:
        #     new_order.count_range = "10+"
        #     new_order.count_range_description = "10+"

        # Insert order

        # Set response
        response.success = True
        response.message = "Order created successfully"
        # response.data = {"order_id": str(result.inserted_id)}

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error in create_order: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while creating order"
        )
