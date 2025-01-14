from datetime import datetime, timedelta, timezone
import time
from typing import List
from venv import logger
from fastapi import APIRouter, HTTPException, Response


from irony.db import db
from irony.models import service
from irony.models.fetch_adaptive_route_vo import FetchAdaptiveRouteRequest
from irony.models.fetch_order_details_vo import FetchOrderDetailsRequest
from irony.models.fetch_orders_vo import FetchOrderRequest
from irony.models.order_status import OrderStatusEnum
from irony.models.service_agent import ServiceAgent, ServiceAgentRegister
from irony.models.update_order_vo import UpdateOrderRequest
from irony.models.user import User
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from irony.models.user_login import UserLogin
from irony.models.user_registration import UserRegistration
from irony.services.Ironman import (
    fetch_adaptive_route_service,
    fetch_order_deatils_service,
    fetch_orders_service,
    service_agent_auth_service,
    update_order_service,
)
from irony.util import auth

router = APIRouter()


@router.post("/login")
async def login(response: Response, user: UserLogin):
    [token, db_user] = await service_agent_auth_service.login_service_agent(
        response, user
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": db_user.model_dump(exclude={"password"}),
    }


@router.post("/register")
async def register(user: ServiceAgentRegister):
    service_agent = await service_agent_auth_service.register_service_agent(user)

    return {
        "message": "User registered successfully",
        "user": service_agent.model_dump(exclude={"password"}),
    }


@router.get("/protected-route")
async def protected_route(current_user: str = Depends(auth.get_current_user)):
    return {"message": f"Welcome, {current_user}!"}


@router.get("/agentOrdersByStatus")
async def getAgentOrdersByStatus(
    current_user: str = Depends(auth.get_current_user), order_status: str = ""
):
    ordered_statuses = [
        OrderStatusEnum(status) for status in order_status.split(",") if status
    ]
    if not ordered_statuses:
        ordered_statuses = [
            OrderStatusEnum.PICKUP_PENDING,
            OrderStatusEnum.WORK_IN_PROGRESS,
            OrderStatusEnum.DELIVERY_PENDING,
        ]
    return await fetch_orders_service.get_orders_by_status_for_agent_locations(
        current_user,
        ordered_statuses=ordered_statuses,
    )


@router.get("/agentOrdersByStatusGroupByStatusAndDateAndTimeSlot")
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


@router.post("/fetchOrderDetails")
async def fetchOrderDetails(request: FetchOrderDetailsRequest):
    return await fetch_order_deatils_service.fetch_order_details(request)


@router.post("/updateOrder")
async def updateOrder(request: UpdateOrderRequest):
    return await update_order_service.update_order(request)


@router.post("/fetchAdaptiveRoute")
async def fetchAdaptiveRoute(request: FetchAdaptiveRouteRequest):
    pass
    # return await fetch_adaptive_route_service.fetch_route(request)
