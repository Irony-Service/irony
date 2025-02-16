from ast import Or
import asyncio
from datetime import date, datetime, timedelta
import json
from math import pi
import pprint
from typing import Any, Dict, List
from urllib import response
import bson
import bson.json_util
from fastapi import HTTPException, Response
from rich import _console

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.order_vo import OrderVo
from irony.models.whatsapp.contact_details import ContactDetails
from irony.config import config
from irony.models.order import Order
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.service_agent.vo.fetch_orders_response import (
    DateItem,
    FetchOrdersResponse,
    FetchOrdersResponseDataItem,
    TimeSlotItem,
)
from irony.models.service_agent.service_agent import ServiceAgent
from irony.services.whatsapp import user_whatsapp_service
from irony.util import pipelines, route, utils, whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger


async def get_orders_for_statuses_group_by_date_and_time_slot_for_agent_locations(
    agent_mobile: str,
    ordered_statuses: List[OrderStatusEnum],
):
    response = FetchOrdersResponse()
    try:
        agent: ServiceAgent = await retrieve_agent_by_mobile_with_service_location(
            agent_mobile
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_orders_group_by_date_and_time_slot_for_service_location_ids(
                agent.service_location_ids, ordered_statuses
            )
        )
        grouped_orders = await db.order.aggregate(pipeline).to_list(None)

        if not grouped_orders:
            response.message = "No orders found"
            return response

        response.data = await get_group_by_date_time_slot_response_body_delivery(
            grouped_orders, ordered_statuses, "Pickup / Delivery"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in get_orders_for_statuses_group_by_date_and_time_slot_for_agent_locations: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching grouped orders",
        )


async def get_orders_for_delivery_with_route(
    agent_mobile: str,
    ordered_statuses: List[OrderStatusEnum],
):
    try:
        response = FetchOrdersResponse()
        agent: ServiceAgent = await retrieve_agent_by_mobile_with_service_location(
            agent_mobile
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_orders_by_status_for_service_location_ids(
                agent.service_location_ids, ordered_statuses
            )
        )

        delivery_orders = await db.order.aggregate(pipeline).to_list(None)

        if not delivery_orders:
            response.message = "No orders found"
            return response

        response.data = await get_response_body_delivery(
            delivery_orders, ordered_statuses, "Pickup / Delivery"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in get_orders_for_statuses_group_by_date_and_time_slot_for_agent_locations: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching grouped orders",
        )


async def retrieve_agent_by_mobile_with_service_location(
    agent_mobile: str,
) -> ServiceAgent:
    agent = await get_agent_by_mobile(agent_mobile)
    if agent.service_location_ids is None:
        raise HTTPException(
            status_code=400, detail="Service agent has no service locations"
        )
    return agent


async def get_agent_by_mobile(agent_mobile) -> ServiceAgent:
    agent_data = await db.service_agent.find_one({"mobile": agent_mobile})
    if agent_data is None:
        raise HTTPException(status_code=404, detail="Service agent not found")

    return ServiceAgent(**agent_data)


async def get_orders_group_by_status_and_date_and_time_slot_for_agent_locations(
    agent_mobile: str,
    ordered_statuses: List[OrderStatusEnum],
) -> FetchOrdersResponse:

    try:
        response = FetchOrdersResponse()

        agent: ServiceAgent = await retrieve_agent_by_mobile_with_service_location(
            agent_mobile
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_orders_group_by_status_and_date_and_time_slot_for_service_location_ids(
                agent.service_location_ids,
                ordered_statuses,
            )
        )
        grouped_orders = await db.order.aggregate(pipeline).to_list(None)

        if not grouped_orders:
            response.message = "No orders founrd"
            return response

        response.data = get_group_by_response_body_agent(
            grouped_orders, ordered_statuses
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unknown Error occurred in fetch orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error occurred in fetch orders")


def get_group_by_response_body_agent(grouped_orders, ordered_statuses):
    response_dict: Dict = {}

    for order_group in grouped_orders:
        if (
            order_group.get("_id") is None
            or order_group.get("_id").get("latest_status") is None
            or order_group.get("_id").get("pick_up_date") is None
            or order_group.get("_id").get("time_slot") is None
            or order_group.get("orders") is None
        ):
            continue

        add_order_to_dict_by_status_date_time_slot_agent(response_dict, order_group)

    response_body: List[FetchOrdersResponseDataItem] = []
    for order_status in ordered_statuses:
        if order_status not in response_dict:
            continue
        status_dict = response_dict[order_status]
        label = OrderStatusEnum.getHomeSectionLabel(order_status)
        date_item_list: List[DateItem] = []
        for date in status_dict:
            date_dict = status_dict[date]
            time_slot_item_list: List[TimeSlotItem] = []
            for time_slot in date_dict:
                time_slot_item_list.append(
                    TimeSlotItem(time_slot=time_slot, orders=date_dict[time_slot])
                )
            date_item_list.append(DateItem(date=date, time_slots=time_slot_item_list))

        response_body.append(
            FetchOrdersResponseDataItem(
                key=order_status, label=label, dates=date_item_list
            )
        )

    return response_body

    respnse_body = [
        response_dict[status] for status in ordered_statuses if status in response_dict
    ]
    return response_dict


def add_order_to_dict_by_status_date_time_slot_agent(response_dict, order_group):
    status = order_group.get("_id").get("latest_status")
    date = order_group.get("_id").get("pick_up_date")
    time_slot = order_group.get("_id").get("time_slot")

    if status not in response_dict:
        response_dict[status] = {}

    if date not in response_dict[status]:
        response_dict[status][date] = {}

    if time_slot not in response_dict[status][date]:
        response_dict[status][date][time_slot] = []

    for order in order_group.get("orders"):
        order = OrderVo(**order)
        order.time_slot_description = (
            config.DB_CACHE.get("call_to_action", {})
            .get(order.time_slot, {})
            .get("title", None)
        )
        order.count_range_description = (
            config.DB_CACHE.get("call_to_action", {})
            .get(order.count_range, {})
            .get("title", None)
        )
        response_dict[status][date][time_slot].append(order)


async def get_group_by_date_time_slot_response_body_delivery(
    grouped_orders, ordered_statuses: List[OrderStatusEnum], label=None
):
    response_dict: dict = {}

    for order_group in grouped_orders:
        if (
            order_group.get("_id") is None
            or not order_group.get("_id").get("pick_up_date")
            or not order_group.get("_id").get("time_slot")
            or not order_group.get("orders")
        ):
            continue

        await add_order_to_dict_by_date_time_slot_delivery(response_dict, order_group)

    response_body: List[FetchOrdersResponseDataItem] = []

    key = "_AND_".join([order_status for order_status in ordered_statuses])
    if not label:
        label = "/".join(
            [
                OrderStatusEnum.getHomeSectionLabel(order_status)
                for order_status in ordered_statuses
            ]
        )

    date_item_list: List[DateItem] = []
    for date in response_dict:
        date_dict = response_dict[date]
        time_slot_item_list: List[TimeSlotItem] = []
        for time_slot in date_dict:
            time_slot_item_list.append(
                TimeSlotItem(time_slot=time_slot, orders=date_dict[time_slot])
            )
        date_item_list.append(DateItem(date=date, time_slots=time_slot_item_list))

    response_body.append(
        FetchOrdersResponseDataItem(key=key, label=label, dates=date_item_list)
    )

    return response_body

    respnse_body = [
        response_dict[date] for date in ordered_statuses if date in response_dict
    ]
    return response_dict


async def add_order_to_dict_by_date_time_slot_delivery(response_dict, order_group):
    date = order_group.get("_id").get("pick_up_date")
    time_slot = order_group.get("_id").get("time_slot")

    if date not in response_dict:
        response_dict[date] = {}

    if time_slot not in response_dict[date]:
        response_dict[date][time_slot] = []

    orders_for_date_and_slot = order_group.get("orders")

    delivery_time_gap = (
        config.DB_CACHE.get("config", {})
        .get("delivery_schedule_time_gap", {})
        .get("value", 60)
    )
    cuttoff_time = datetime.now() + timedelta(minutes=delivery_time_gap)

    route_required = False
    order_list_for_date_and_slot: List[Order] = []
    for order in orders_for_date_and_slot:
        order = OrderVo(**order)

        if (
            not route_required
            and order.pickup_date_time.start
            and order.pickup_date_time.start < cuttoff_time
        ):
            route_required = True

        order.time_slot_description = (
            config.DB_CACHE.get("call_to_action", {})
            .get(order.time_slot, {})
            .get("title", None)
        )
        order.count_range_description = (
            config.DB_CACHE.get("call_to_action", {})
            .get(order.count_range, {})
            .get("title", None)
        )
        order.delivery_type = OrderStatusEnum.getDeliveryType(
            order.order_status[0].status
        )
        order.maps_link = utils.get_maps_link(order.location)

        order_list_for_date_and_slot.append(order)

    if route_required:
        try:
            order_list_for_date_and_slot = await route.route_sort_orders(
                order_list_for_date_and_slot
            )
            logger.info(f"Route sorted orders: {order_list_for_date_and_slot}")
        except HTTPException as e:
            handle_route_error(order_list_for_date_and_slot, e)

    response_dict[date][time_slot] = order_list_for_date_and_slot


# CONTINUE FROM HERE
async def get_response_body_delivery(
    orders, ordered_statuses: List[OrderStatusEnum], label=None
):
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    response_dict: dict = {now: {}}
    delivery_time_gap = (
        config.DB_CACHE.get("config", {})
        .get("delivery_schedule_time_gap", {})
        .get("value", 60)
    )
    cuttoff_time = datetime.now() + timedelta(minutes=delivery_time_gap)
    pickup_time_start = None

    order_list_for_date_and_slot: List[Order] = []
    for order in orders:
        order = OrderVo(**order)

        if (
            not pickup_time_start
            and order.pickup_date_time.start
            and order.pickup_date_time.start < cuttoff_time
        ):
            pickup_time_start = order.pickup_date_time.start

        order.time_slot_description = (
            config.DB_CACHE.get("call_to_action", {})
            .get(order.time_slot, {})
            .get("title", None)
        )
        order.count_range_description = (
            config.DB_CACHE.get("call_to_action", {})
            .get(order.count_range, {})
            .get("title", None)
        )
        order.delivery_type = OrderStatusEnum.getDeliveryType(
            order.order_status[0].status
        )
        order.maps_link = utils.get_maps_link(order.location)

        order_list_for_date_and_slot.append(order)

    if pickup_time_start:
        try:
            order_list_for_date_and_slot = await route.route_sort_orders(
                order_list_for_date_and_slot
            )
            logger.info(f"Route sorted orders: {order_list_for_date_and_slot}")
        except HTTPException as e:
            handle_route_error(order_list_for_date_and_slot, e)

    response_dict[now]["Routes"] = order_list_for_date_and_slot

    response_body = []
    key = "_AND_".join([order_status for order_status in ordered_statuses])
    if not label:
        label = "/".join(
            [
                OrderStatusEnum.getHomeSectionLabel(order_status)
                for order_status in ordered_statuses
            ]
        )

    # for order_status in ordered_statuses:
    #     if order_status not in response_dict:
    #         continue
    #     status_obj = response_dict[order_status]
    date_item_list: List[DateItem] = []
    for date in response_dict:
        date_obj = response_dict[date]
        time_slot_item_list: List[TimeSlotItem] = []
        for time_slot in date_obj:
            time_slot_item_list.append(
                TimeSlotItem(time_slot=time_slot, orders=date_obj[time_slot])
            )
        date_item_list.append(DateItem(date=date, time_slots=time_slot_item_list))

    response_body.append(
        FetchOrdersResponseDataItem(key=key, label=label, dates=date_item_list)
    )

    return response_body

    respnse_body = [
        response_dict[date] for date in ordered_statuses if date in response_dict
    ]
    return response_dict


def handle_route_error(order_list_for_date_and_slot, e):
    if e.status_code == 400:
        if e.detail == "No route found":
            asyncio.create_task(
                db.route_exceptions.insert_one(
                    {
                        "status_code": e.status_code,
                        "order_ids": [
                            order.id for order in order_list_for_date_and_slot
                        ],
                        "details": e.detail,
                        "created_at": datetime.now(),
                    }
                )
            )
            logger.error(f"No route found for orders: {order_list_for_date_and_slot}")
