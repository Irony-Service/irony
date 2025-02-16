from typing import Any, Dict, List
from fastapi import APIRouter, Response


from irony.config import config
from irony.config.logger import logger
from irony.db import db
from irony.models.service_agent.vo.auth.register_request import AgentRegisterRequest
from irony.models.service_agent.vo.auth.register_response import AgentRegisterResponse
from irony.models.service_agent.vo.fetch_adaptive_route_vo import (
    FetchAdaptiveRouteRequest,
)
from irony.models.service_agent.vo.fetch_order_details_vo import (
    FetchOrderDetailsRequest,
)
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.service import Service
from irony.models.service_agent.service_agent import ServiceAgent
from irony.models.prices import Prices
from irony.models.service_agent.vo.auth.login_response import AgentLoginResponse
from irony.models.service_agent.vo.fetch_orders_response import FetchOrdersResponse
from irony.models.service_agent.vo.prices_response_vo import (
    PricesResponseVo,
    ServicePrices,
)
from irony.models.service_agent.vo.update_pickup_pending_vo import UpdateOrderRequest
from fastapi import Depends

from irony.models.service_agent.vo.auth.login_request import AgentLoginRequest
from irony.services.agent import (
    agent_auth_service,
    fetch_order_deatils_service,
    fetch_orders_service,
    service_prices_service,
    create_update_order_service,
)
from irony.util import auth

from irony.models.service_agent.vo.create_order_vo import (
    CreateOrderRequest,
    CreateOrderResponse,
)

router = APIRouter()


@router.post("/register", response_model=AgentRegisterResponse)
async def register(user: AgentRegisterRequest):
    return await agent_auth_service.register_service_agent(user)


@router.post("/login", response_model=AgentLoginResponse)
async def login(response: Response, request: AgentLoginRequest):
    return await agent_auth_service.login_service_agent(response, request)


@router.get(
    "/agentOrdersByStatusGroupByStatusAndDateAndTimeSlot",
    response_model=FetchOrdersResponse,
)
async def getAgentOrdersByStatusGroupByStatusAndDateAndTimeSlot(
    current_user: str = Depends(auth.get_current_user), order_status: str = ""
):
    ordered_statuses: List[OrderStatusEnum] = [
        OrderStatusEnum(status) for status in order_status.split(",") if status
    ]
    if not ordered_statuses:
        ordered_statuses = [
            OrderStatusEnum.PICKUP_PENDING,
            OrderStatusEnum.WORK_IN_PROGRESS,
            OrderStatusEnum.DELIVERY_PENDING,
        ]
    return await fetch_orders_service.get_orders_group_by_status_and_date_and_time_slot_for_agent_locations(
        current_user,
        ordered_statuses=ordered_statuses,
    )


@router.get("/agentOrdersByStatusGroupByDateAndTimeSlot")
async def getAgentOrdersByStatusGroupByDateAndTimeSlot(
    current_user: str = Depends(auth.get_current_user), order_status: str = ""
):
    ordered_statuses: List[OrderStatusEnum] = [
        OrderStatusEnum(status) for status in order_status.split(",") if status
    ]
    if not ordered_statuses:
        ordered_statuses = [
            OrderStatusEnum.PICKUP_PENDING,
            OrderStatusEnum.DELIVERY_PENDING,
        ]
    return await fetch_orders_service.get_orders_for_statuses_group_by_date_and_time_slot_for_agent_locations(
        current_user,
        ordered_statuses=ordered_statuses,
    )


@router.get("/agentOrdersForDeliveryWithRoute")
async def getAgentOrdersForDeliveryWithRoute(
    current_user: str = Depends(auth.get_current_user),
):

    ordered_statuses = [
        OrderStatusEnum.PICKUP_PENDING,
        OrderStatusEnum.DELIVERY_PENDING,
    ]
    return await fetch_orders_service.get_orders_for_delivery_with_route(
        current_user,
        ordered_statuses=ordered_statuses,
    )


@router.get("/servicePricesForServiceLocations")
async def getServicePricesForServiceLocations(
    current_user: str = Depends(auth.get_current_user),
):
    return await service_prices_service.get_service_prices_for_locations(current_user)


@router.post("/fetchOrderDetails")
async def fetchOrderDetails(request: FetchOrderDetailsRequest):
    return await fetch_order_deatils_service.fetch_order_details(request)


@router.post("/createOrder", response_model=CreateOrderResponse)
async def createOrder(request: CreateOrderRequest):
    return await create_update_order_service.create_order(request)


@router.post("/updateOrder")
async def updateOrder(request: UpdateOrderRequest):
    return await create_update_order_service.update_order(request)


@router.post("/fetchAdaptiveRoute")
async def fetchAdaptiveRoute(request: FetchAdaptiveRouteRequest):
    pass
    # return await fetch_adaptive_route_service.fetch_route(request)


@router.get("/protected-route")
async def protected_route(current_user: str = Depends(auth.get_current_user)):
    return {"message": f"Welcome, {current_user}!"}
