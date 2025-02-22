import copy
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from pymongo import DeleteOne, InsertOne, ReplaceOne

from irony.config import config
from irony.config.logger import logger
from irony.db import bulk_write_operations, db
from irony.models.order import Order
from irony.models.order_item import OrderItem
from irony.models.order_status import OrderStatus
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.pickup_tIme import PickupDateTime
from irony.models.prices import Prices
from irony.models.pyobjectid import PyObjectId
from irony.models.service import Service
from irony.models.service_agent.vo.create_order_vo import CreateOrderRequest
from irony.models.service_agent.vo.order_request_vo import (
    CommonOrderRequest,
    CommonOrderResponse,
    CommonOrderResponseBody,
)
from irony.models.service_agent.vo.update_pickup_pending_vo import (
    UpdateOrderRequest,
    UpdateOrderResponse,
)
from irony.models.user import User


async def update_order(request: UpdateOrderRequest) -> UpdateOrderResponse:
    """Update an existing order with new status and details.

    Args:
        request (UpdateOrderRequest): Request containing order update details including order_id,
            current_status, new_status, and other optional fields.

    Returns:
        UpdateOrderResponse: Response containing updated order details.

    Raises:
        HTTPException: If validation fails or there's an error during update.
    """
    try:
        response = UpdateOrderResponse()
        now = datetime.now()

        _validate_update_order_request(request)

        order = await _get_order(request.order_id)

        latest_order_status = _validate_fetched_order_for_update_order(request, order)

        # Execute bulk operations outside the loop
        bulk_operations: List[ReplaceOne | InsertOne | DeleteOne] = []
        if latest_order_status == OrderStatusEnum.PICKUP_PENDING:
            _validate_common_order_request(request)
            await _process_pending_pickup_order_update(
                request, response, now, order, bulk_operations
            )

        if latest_order_status == OrderStatusEnum.WORK_IN_PROGRESS:
            if request.new_status == OrderStatusEnum.DELIVERY_PENDING:
                await _update_order_status(request, now, order, bulk_operations)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition from WORK_IN_PROGRESS",
                )

        elif latest_order_status == OrderStatusEnum.DELIVERY_PENDING:
            if request.new_status == OrderStatusEnum.DELIVERED:
                await _update_order_status(request, now, order, bulk_operations)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition from DELIVERY_PENDING",
                )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in update_order: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while updating order"
        ) from e


async def create_order(request: CreateOrderRequest) -> CommonOrderResponse:
    """Create a new order in the system.

    Args:
        request (CreateOrderRequest): Request containing order details including user info,
            items, prices, and service location.

    Returns:
        CommonOrderResponse: Response containing created order details including order IDs.

    Raises:
        HTTPException: If validation fails or there's an error during creation.
    """
    try:
        response = CommonOrderResponse()
        now = datetime.now()

        _validate_create_order_request(request)

        price_map = await _get_price_map_for_request(request)
        _validate_price(request, price_map)

        service_grouped_items = _get_items_grouped_by_service(request, price_map)

        # Check if user exists, create if not
        user_id = await _get_or_create_user(request, now)
        time_slot_id, pickup_date_time = _get_timeslot_and_pickup_date_time(now)

        # Create new order
        new_order = _get_new_order(
            request, now, user_id, time_slot_id, pickup_date_time
        )

        bulk_operations: List[InsertOne] = []
        order_list: List[Order] = []
        order_id_list = []
        sub_id_dict: Optional[Dict] = None

        if len(service_grouped_items.keys()) > 1:
            sub_id_dict = {}
            _process_service_grouped_orders(
                service_grouped_items,
                new_order,
                bulk_operations,
                order_list,
                order_id_list,
                sub_id_dict,
            )

            # Execute all operations in a transaction
            await bulk_write_operations("order", bulk_operations)

            new_order.child_order_ids = order_id_list
            result = await db.parent_order.insert_one(
                new_order.model_dump(exclude_unset=True, by_alias=True)
            )
        else:
            result = await db.order.insert_one(
                new_order.model_dump(exclude_unset=True, by_alias=True)
            )
            order_id_list.append(str(result.inserted_id))
            order_list.append(new_order)

        response.data = CommonOrderResponseBody(
            sub_id_dict=sub_id_dict, order_ids=order_id_list
        )

        response.message = "Order created successfully"

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Error in create_order: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while creating order"
        ) from e


async def _process_pending_pickup_order_update(
    request: UpdateOrderRequest,
    response: UpdateOrderResponse,
    now: datetime,
    order: Order,
    bulk_operations: List[ReplaceOne | InsertOne | DeleteOne],
):
    """Process order updates when the order is in PICKUP_PENDING status.

    Args:
        request (UpdateOrderRequest): Update request details
        response (UpdateOrderResponse): Response object to be updated
        now (datetime): Current timestamp
        order (Order): Current order object
        bulk_operations (List): List of MongoDB operations to be executed

    Raises:
        HTTPException: If there's an error during processing
    """
    if request.new_status == OrderStatusEnum.WORK_IN_PROGRESS:
        price_map = await _get_price_map_for_request(request)
        _validate_price(request, price_map)

        service_grouped_items = _get_items_grouped_by_service(request, price_map)

        order.order_status.insert(  # type: ignore
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

        await _update_location_nickname(order, request.location_nickname)

        order_list: List[Order] = []
        order_id_list = []
        sub_id_dict: Optional[Dict] = None
        # If more than 1 service chooosed.
        if len(service_grouped_items.keys()) > 1:
            sub_id_dict = {}
            _process_service_grouped_orders(
                service_grouped_items,
                order,
                bulk_operations,
                order_list,
                order_id_list,
                sub_id_dict,
            )

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
            _set_order_item_details(order, request.items)
            await db.order.replace_one(
                {"_id": PyObjectId(request.order_id)},
                order.model_dump(exclude_unset=True, by_alias=True),
            )
            order_id_list.append(str(order.id))
            order_list.append(order)

        response.data = CommonOrderResponseBody(
            sub_id_dict=sub_id_dict, order_ids=order_id_list
        )
    if request.new_status in (
        OrderStatusEnum.PICKUP_USER_NO_RESP,
        OrderStatusEnum.PICKUP_USER_REJECTED,
    ):
        order.order_status.insert(  # type: ignore
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


def _validate_fetched_order_for_update_order(
    request: UpdateOrderRequest, order: Order
) -> OrderStatusEnum:
    """Validate the fetched order against update request.

    Args:
        request (UpdateOrderRequest): Update request details
        order (Order): Order to be validated

    Returns:
        OrderStatusEnum: Current status of the order

    Raises:
        HTTPException: If validation fails
    """
    if not order.order_status or len(order.order_status) == 0:
        raise HTTPException(status_code=400, detail="Order status not found")
    latest_order_status = order.order_status[0].status
    if latest_order_status != OrderStatusEnum(request.current_status):
        raise HTTPException(
            status_code=400,
            detail="Status for this order has changed. Please refresh the page.",
        )

    return latest_order_status  # type: ignore


def _validate_update_order_request(request: UpdateOrderRequest):
    """Validate the update order request parameters.

    Args:
        request (UpdateOrderRequest): Request to be validated

    Raises:
        HTTPException: If validation fails
    """
    if not request.order_id:
        raise HTTPException(status_code=400, detail="Order ID not provided")
    if not request.current_status or not request.new_status:
        raise HTTPException(status_code=400, detail="Status not provided")
    if (
        request.current_status not in OrderStatusEnum.__members__.values()
        or request.new_status not in OrderStatusEnum.__members__.values()
    ):
        raise HTTPException(status_code=400, detail="Invalid status provided")

    if request.current_status == request.new_status:
        raise HTTPException(
            status_code=400, detail="Current status and new status are same"
        )


async def _get_order(order_id: str) -> Order:
    """Fetch order by ID from database.

    Args:
        order_id (str): ID of the order to fetch

    Returns:
        Order: Found order object

    Raises:
        HTTPException: If order not found
    """
    order_data = await db.order.find_one({"_id": PyObjectId(order_id)})
    if order_data is None:
        raise HTTPException(status_code=404, detail="Order not found")

    order = Order(**order_data)
    return order


async def _update_order_status(
    request: UpdateOrderRequest, now: datetime, order: Order, bulk_operations: List
):
    """Update order status with new status.

    Args:
        request (UpdateOrderRequest): Update request details
        now (datetime): Current timestamp
        order (Order): Order to be updated
        bulk_operations (List): List of MongoDB operations
    """
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


def _get_clone_order_if_required(
    order: Order,
    is_new_instance: bool,
    is_new_id: bool,
) -> Order:
    """Clone order object based on requirements.

    Args:
        order (Order): Original order object
        is_new_instance (bool): Whether to create new instance
        is_new_id (bool): Whether to generate new ID

    Returns:
        Order: Cloned order object
    """
    order_instance = order
    if is_new_instance:
        order_instance = copy.deepcopy(order)
    if is_new_id:
        order_instance.id = PyObjectId()
        # order_instance.order_items = None
    return order_instance


def _set_order_item_details_and_sub_id(
    sevice_grouped_item: tuple[str, List[OrderItem]], order_instance: Order
):
    order_instance.sub_id = str(sevice_grouped_item[0])[:2]
    _set_order_item_details(order_instance, sevice_grouped_item[1])


def _set_order_item_details(order_instance: Order, order_items: List[OrderItem]):
    order_instance.order_items = order_items
    order_instance.total_count = sum(item.count for item in order_items)
    order_instance.total_price = sum(item.amount for item in order_items)


def _validate_price(request: CommonOrderRequest, price_map: Dict[str, Prices]):
    """Validate prices of order items against price map.

    Args:
        request (CommonOrderRequest): Request containing items
        price_map (Dict[str, Prices]): Map of price IDs to price objects

    Raises:
        HTTPException: If price validation fails
    """
    price = 0.0

    for item in request.items:
        if item and item.amount:
            if (item.amount / item.count) != price_map[item.price_id].price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Price mismatch for item: {item.price_id}",
                )
            price += item.amount

    if request.total_price != price:
        raise HTTPException(status_code=400, detail="Total price mismatch")


def _get_items_grouped_by_service(
    request: CommonOrderRequest, price_map: Dict[str, Prices]
) -> Dict[str, List[OrderItem]]:
    """Group order items by their associated service.

    Args:
        request (CommonOrderRequest): Request containing items
        price_map (Dict[str, Prices]): Map of price IDs to price objects

    Returns:
        Dict[str, List[OrderItem]]: Items grouped by service ID
    """
    service_grouped_items: Dict[str, List[OrderItem]] = {}

    for item in request.items:
        associated_service_id = str(price_map[item.price_id].service_id)
        if associated_service_id not in service_grouped_items:
            service_grouped_items[associated_service_id] = []
        service_grouped_items[associated_service_id].append(item)

    return service_grouped_items


async def _update_location_nickname(order: Order, location_nickname: Optional[str]):
    """Update location nickname in order and location collection.

    Args:
        order (Order): Order containing location
        location_nickname (Optional[str]): New nickname for location
    """
    if location_nickname and order.location:
        order.location.nickname = location_nickname
        # Update nickname for existing location document
        await db.location.update_one(
            {"_id": order.location.id}, {"$set": {"nickname": location_nickname}}
        )
        # check if need to udpate location in user


def _get_timeslot_and_pickup_date_time(
    pickup_datetime: datetime,
) -> tuple[str, PickupDateTime]:
    """Calculate time slot and pickup datetime based on current time.

    Args:
        pickup_datetime (datetime): Base datetime for calculation

    Returns:
        tuple[str, PickupDateTime]: Time slot ID and pickup datetime object

    Raises:
        HTTPException: If time slot calculation fails
    """
    time_slot_id = None
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

    if not time_slot_id:
        raise HTTPException(
            status_code=500,
            detail="Unable to create order (time_slot_id issue). Please try again later",
        )

    start_time = pickup_datetime.replace(hour=h, minute=m, second=0, microsecond=0)
    end_time = pickup_datetime.replace(hour=he, minute=me, second=0, microsecond=0)
    date_time = pickup_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    pickup_date_time = PickupDateTime(
        date=date_time,
        start=start_time,
        end=end_time,
    )

    return time_slot_id, pickup_date_time


def _process_service_grouped_orders(
    service_grouped_items: Dict[str, List[OrderItem]],
    new_order: Order,
    bulk_operations: List,
    order_list: List[Order],
    order_id_list: List,
    sub_id_dict: Optional[Dict],
):
    for service_grouped_item in service_grouped_items.items():
        order_instance: Order = _get_clone_order_if_required(new_order, True, False)

        _set_order_item_details_and_sub_id(service_grouped_item, order_instance)

        order_dict = order_instance.model_dump(
            exclude_unset=True,
            by_alias=True,
            exclude={"id"},
        )
        bulk_operations.append(InsertOne(order_dict))

        _update_response_order_id_and_sub_ids(
            order_list,
            order_id_list,
            sub_id_dict,
            service_grouped_item,
            order_instance,
        )


def _validate_create_order_request(request: CreateOrderRequest):
    """Validate create order request parameters.

    Args:
        request (CreateOrderRequest): Request to be validated

    Raises:
        HTTPException: If validation fails
    """
    _validate_common_order_request(request)
    if not request.user_wa_id:
        raise HTTPException(status_code=400, detail="Mobile number is required")
    if not request.user_wa_id.isdigit() or len(request.user_wa_id) != 10:
        raise HTTPException(
            status_code=400, detail="Invalid mobile number. Must be 10 digits"
        )
    if not request.service_location_id:
        raise HTTPException(status_code=400, detail="Service location is required")


def _validate_common_order_request(request: CommonOrderRequest):
    if not request.items:
        raise HTTPException(status_code=400, detail="Please add items to order")


async def _get_price_map_for_request(request: CommonOrderRequest) -> Dict[str, Prices]:
    """Create price map for items in request.

    Args:
        request (CommonOrderRequest): Request containing items

    Returns:
        Dict[str, Prices]: Map of price IDs to price objects
    """
    # Create a price_map for quick lookup
    price_map: Dict[str, Prices] = {
        str(price["_id"]): Prices(**price)
        for price in await db.prices.find(
            {"_id": {"$in": [PyObjectId(item.price_id) for item in request.items]}}
        ).to_list(None)
    }

    return price_map


def _update_response_order_id_and_sub_ids(
    order_list: List[Order],
    order_id_list: List,
    sub_id_dict: Optional[Dict],
    service_grouped_item: tuple[str, List[OrderItem]],
    order_instance: Order,
):
    """Update response data with order IDs and sub-IDs.

    Args:
        order_list (List[Order]): List of orders
        order_id_list (List): List of order IDs
        sub_id_dict (Optional[Dict]): Dictionary of sub-IDs
        service_grouped_item (tuple[str, List[OrderItem]]): Service and its items
        order_instance (Order): Current order instance
    """
    service: Service = config.DB_CACHE["id_to_service_map"][service_grouped_item[0]]
    sub_id_dict[service.service_name] = order_instance.sub_id  # type: ignore
    order_id_list.append(str(order_instance.id))
    order_list.append(order_instance)


def _get_new_order(
    request: CreateOrderRequest,
    now: datetime,
    user_id: str | PyObjectId,
    time_slot_id: str,
    pickup_date_time: PickupDateTime,
) -> Order:
    """Create new order instance from request data.

    Args:
        request (CreateOrderRequest): Order creation request
        now (datetime): Current timestamp
        user_id (str | PyObjectId): ID of the user
        time_slot_id (str): Selected time slot ID
        pickup_date_time (PickupDateTime): Pickup datetime object

    Returns:
        Order: New order instance
    """
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
    return new_order


async def _get_or_create_user(request: CreateOrderRequest, now) -> str | PyObjectId:
    """Get existing user or create new user from request.

    Args:
        request (CreateOrderRequest): Request containing user details
        now: Current timestamp

    Returns:
        str | PyObjectId: User ID

    Raises:
        HTTPException: If user creation fails
    """
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
    if not user_id:
        raise HTTPException(
            status_code=500,
            detail="Unable to create order (user_id issue). Please try again later",
        )
    return user_id
