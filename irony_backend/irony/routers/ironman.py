from typing import List

from fastapi import APIRouter, Depends, Response

from irony.models.order_status_enum import OrderStatusEnum
from irony.models.service_agent.vo.auth.login_request import AgentLoginRequest
from irony.models.service_agent.vo.auth.login_response import AgentLoginResponse
from irony.models.service_agent.vo.auth.register_request import AgentRegisterRequest
from irony.models.service_agent.vo.auth.register_response import AgentRegisterResponse
from irony.models.service_agent.vo.create_order_vo import CreateOrderRequest
from irony.models.service_agent.vo.fetch_orders_response import FetchOrdersResponse
from irony.models.service_agent.vo.order_request_vo import CommonOrderResponse
from irony.models.service_agent.vo.update_pickup_pending_vo import UpdateOrderRequest
from irony.services.agent import auth_service, service_service
from irony.services.agent.order import create_update_order_service, fetch_orders_service
from irony.util import auth

router = APIRouter()

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


# Authentication endpoints
@router.post("/register", response_model=AgentRegisterResponse)
async def register(user: AgentRegisterRequest):
    """
    Register a new service agent.

    Args:
        user (AgentRegisterRequest): Registration details for the new agent

    Returns:
        AgentRegisterResponse: Registration confirmation details
    """
    return await auth_service.register_service_agent(user)


@router.post("/login", response_model=AgentLoginResponse)
async def login(response: Response, request: AgentLoginRequest):
    """
    Authenticate a service agent.

    Args:
        response (Response): FastAPI response object for setting cookies
        request (AgentLoginRequest): Login credentials

    Returns:
        AgentLoginResponse: Authentication token and user details
    """
    return await auth_service.login_service_agent(response, request)


# Order management endpoints
@router.get(
    "/agentOrdersByStatusGroupByStatusAndDateAndTimeSlot",
    response_model=FetchOrdersResponse,
)
async def get_agent_orders_by_status_group_by_status_and_date_and_time_slot(
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


@router.get(
    "/agentOrdersByStatusGroupByDateAndTimeSlot", response_model=FetchOrdersResponse
)
async def get_agent_orders_by_status_group_by_date_and_time_slot(
    current_user: str = Depends(auth.get_current_user), order_status: str = ""
):
    """
    Fetch and group orders by date and time slot for an agent.

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
    )


@router.get("/agentOrdersForDeliveryWithRoute")
async def get_agent_orders_for_delivery_with_route(
    current_user: str = Depends(auth.get_current_user),
):
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


@router.get("/servicePricesForServiceLocations")
async def get_service_prices_for_service_locations(
    current_user: str = Depends(auth.get_current_user),
):
    """
    Get service prices for available service locations.

    Args:
        current_user (str): Authenticated user ID

    Returns:
        dict: Service prices by location
    """
    return await service_service.get_service_prices_for_locations(current_user)


# @router.post("/fetchOrderDetails")
# async def fetch_order_details(request: FetchOrderDetailsRequest):
#     """
#     Fetch detailed information for a specific order.

#     Args:
#         request (FetchOrderDetailsRequest): Order lookup parameters

#     Returns:
#         dict: Detailed order information
#     """
#     return await fetch_order_deatils_service.fetch_order_details(request)


@router.post("/createOrder", response_model=CommonOrderResponse)
async def create_order(request: CreateOrderRequest):
    """
    Create a new order in the system.

    Args:
        request (CreateOrderRequest): Order creation details

    Returns:
        CommonOrderResponse: Created order details
    """
    return await create_update_order_service.create_order(request)


@router.post("/updateOrder")
async def update_order(request: UpdateOrderRequest):
    """
    Update an existing order's details.

    Args:
        request (UpdateOrderRequest): Order update parameters

    Returns:
        dict: Updated order details
    """
    return await create_update_order_service.update_order(request)


@router.get("/protected-route")
async def protected_route(current_user: str = Depends(auth.get_current_user)):
    """
    Test endpoint for authenticated users.

    Args:
        current_user (str): Authenticated user ID

    Returns:
        dict: Welcome message with user ID
    """
    return {"message": f"Welcome, {current_user}!"}
