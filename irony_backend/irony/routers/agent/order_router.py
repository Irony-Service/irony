from typing import List

from fastapi import APIRouter, Depends

from irony.models.order_status_enum import OrderStatusEnum
from irony.models.service_agent.vo.create_order_vo import CreateOrderRequest
from irony.models.service_agent.vo.fetch_order_details_vo import (
    FetchOrderDetailsResponse,
)
from irony.models.service_agent.vo.fetch_orders_response import FetchOrdersResponse
from irony.models.service_agent.vo.order_request_vo import CommonOrderResponse
from irony.models.service_agent.vo.update_pickup_pending_vo import (
    UpdateOrderRequest,
    UpdateOrderResponse,
)
from irony.services.agent.order import (
    create_update_order_service,
    fetch_order_deatils_service,
    fetch_orders_service,
)
from irony.util import auth

router = APIRouter(prefix="/orders", tags=["Orders"])

# Constants
DEFAULT_ORDER_STATUSES = {
    "delivery": [OrderStatusEnum.PICKUP_PENDING, OrderStatusEnum.DELIVERY_PENDING],
    "all": [
        OrderStatusEnum.PICKUP_PENDING,
        OrderStatusEnum.WORK_IN_PROGRESS,
        OrderStatusEnum.DELIVERY_PENDING,
    ],
}


def parse_order_statuses(
    status_string: str, default_type: str = "all"
) -> List[OrderStatusEnum]:
    """Helper function to parse order status strings into enums"""
    if not status_string:
        return DEFAULT_ORDER_STATUSES[default_type]
    return [OrderStatusEnum(status) for status in status_string.split(",") if status]


@router.get("/by-status-date-timeslot", response_model=FetchOrdersResponse)
async def get_by_status_and_date_and_time_slot(
    current_user: str = Depends(auth.get_current_user), order_status: str = ""
) -> FetchOrdersResponse:
    """
    Fetch and group orders by status, date and time slot for an agent.

    Args:
        current_user (str): Authenticated user ID
        order_status (str): Comma-separated list of order statuses to filter

    Returns:
        FetchOrdersResponse: Grouped orders matching the criteria
    """
    ordered_statuses = parse_order_statuses(order_status)
    return await fetch_orders_service.get_orders_group_by_status_and_date_and_time_slot(
        current_user,
        ordered_statuses=ordered_statuses,
    )


@router.get("/delivery-schedule", response_model=FetchOrdersResponse)
async def get_delivery_schedule(
    current_user: str = Depends(auth.get_current_user), order_status: str = ""
) -> FetchOrdersResponse:
    """
    Get delivery schedule grouped by date and time slot

    Args:
        current_user (str): Authenticated user ID
        order_status (str): Comma-separated list of order statuses to filter

    Returns:
        FetchOrdersResponse: Orders grouped by date and time slot
    """
    ordered_statuses = parse_order_statuses(order_status, default_type="delivery")
    return await fetch_orders_service.get_orders_group_by_date_and_time_slot_routable(
        current_user,
        ordered_statuses=ordered_statuses,
        route_required=True,
    )


@router.get("/delivery-route", response_model=FetchOrdersResponse)
async def get_delivery_route(
    current_user: str = Depends(auth.get_current_user),
) -> FetchOrdersResponse:
    """
    Fetch delivery orders with optimized route information.

    Args:
        current_user (str): Authenticated user ID

    Returns:
        dict: Orders with route optimization details
    """
    ordered_statuses = DEFAULT_ORDER_STATUSES["delivery"]
    return await fetch_orders_service.get_orders_for_delivery_with_route(
        current_user,
        ordered_statuses=ordered_statuses,
    )


@router.get("/{order_id}", response_model=FetchOrderDetailsResponse)
async def get_order(order_id: str) -> FetchOrderDetailsResponse:
    """
    Fetch detailed information for a specific order.

    Args:
        order_id (str): Order ID to fetch details for

    Returns:
        dict: Detailed order information
    """
    return await fetch_order_deatils_service.fetch_order_details(order_id)


@router.post("", response_model=CommonOrderResponse)
async def create_order(request: CreateOrderRequest) -> CommonOrderResponse:
    """
    Create a new order in the system.

    Args:
        request (CreateOrderRequest): Order creation details

    Returns:
        CommonOrderResponse: Created order details
    """
    return await create_update_order_service.create_order(request)


@router.put("", response_model=UpdateOrderResponse)
async def update_order(request: UpdateOrderRequest) -> UpdateOrderResponse:
    """
    Update an existing order's details.

    Args:
        request (UpdateOrderRequest): Order update parameters

    Returns:
        dict: Updated order details
    """
    return await create_update_order_service.update_order(request)
