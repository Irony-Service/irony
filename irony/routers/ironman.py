from typing import Any, Dict, List
from fastapi import APIRouter, Response


from irony.config import config
from irony.config.logger import logger
from irony.db import db
from irony.models.fetch_adaptive_route_vo import FetchAdaptiveRouteRequest
from irony.models.fetch_order_details_vo import FetchOrderDetailsRequest
from irony.models.order_status import OrderStatusEnum
from irony.models.service import Service
from irony.models.service_agent.service_agent import ServiceAgent, ServiceAgentRegister
from irony.models.service_agent.prices import Prices
from irony.models.service_agent.prices_response_vo import (
    PricesResponseVo,
    ServicePrices,
)
from irony.models.update_pickup_pending_vo import UpdateOrderRequest
from fastapi import Depends

from irony.models.user_login import UserLogin
from irony.services.Ironman import (
    fetch_order_deatils_service,
    fetch_orders_service,
    service_agent_auth_service,
    update_pickup_pending_service,
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


@router.get("/servicePricesForServiceLocations")
async def getServicePricesForServiceLocations(
    current_user: str = Depends(auth.get_current_user),
):
    response = PricesResponseVo()
    services: Dict[str, Service] = {
        str(service.id): service
        for service in config.DB_CACHE.get("services", {}).values()
    }
    agent_data = await db.service_agent.find_one({"mobile": current_user})
    if agent_data is None:
        raise Exception("Service agent not found")

    agent: ServiceAgent = ServiceAgent(**agent_data)

    if agent.service_location_ids is None:
        raise Exception("Service agent has no service locations")

    pipeline: List[Dict[str, Any]] = [
        {
            "$match": {
                "service_location_id": {"$in": agent.service_location_ids},
            }
        },
        {"$sort": {"sort_order": 1}},
        {
            "$group": {
                "_id": {
                    "service_location_id": "$service_location_id",
                    "service_id": "$service_id",
                },
                "prices": {"$push": "$$ROOT"},
            }
        },
    ]

    prices_groups = await db.prices.aggregate(pipeline=pipeline).to_list(None)

    if not prices_groups:
        response.success = False
        response.error = "No orders found"
        return response.model_dump()

    service_location_service_prices: Dict[str, Dict[str, List[Prices]]] = {}

    for price_group in prices_groups:
        service_location_id = str(price_group.get("_id", {}).get("service_location_id"))
        service_id = str(price_group.get("_id", {}).get("service_id"))

        if service_location_id not in service_location_service_prices:
            service_location_service_prices[service_location_id] = {}
        service_location_service_prices[service_location_id][service_id] = [
            Prices(**price_item) for price_item in price_group.get("prices", [])
        ]

    response_body: Dict[str, List[ServicePrices]] = {}
    for (
        service_location_id,
        service_prices,
    ) in service_location_service_prices.items():
        service_prices_list: List[ServicePrices] = []
        for service_id, prices in service_prices.items():
            service = services.get(service_id)
            if service:
                service_prices_list.append(
                    ServicePrices(
                        service=service,
                        prices=prices,
                    )
                )
        service_prices_list.sort(key=lambda x: x.service.call_to_action_key or "")
        response_body[service_location_id] = service_prices_list

    response.success = True
    response.body = response_body
    # response.body = PricesResponseBody(
    #     service_locations_prices=service_location_service_prices, services=services
    # )
    # response.body = service_location_service_prices

    return response.model_dump()


@router.post("/fetchOrderDetails")
async def fetchOrderDetails(request: FetchOrderDetailsRequest):
    return await fetch_order_deatils_service.fetch_order_details(request)


@router.post("/updateOrder")
async def updateOrder(request: UpdateOrderRequest):
    return await update_pickup_pending_service.update_order(request)


@router.post("/fetchAdaptiveRoute")
async def fetchAdaptiveRoute(request: FetchAdaptiveRouteRequest):
    pass
    # return await fetch_adaptive_route_service.fetch_route(request)
