from datetime import date
import pprint
from typing import Any, Dict, List
from urllib import response
from bson import ObjectId
from fastapi import Response
from rich import _console

from irony.db import db, replace_documents_in_transaction
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.config import config
from irony.models.order import Order
from irony.models.order_status import OrderStatusEnum
from irony.models.fetch_orders_vo import (
    DateItem,
    FetchOrderRequest,
    FetchOrderResponseBody,
    FetchOrdersResponse,
    FetchOrdersResponseBodyItem,
    FetchOrdersResponseBodyItem1,
    OrderChunk,
    TimeSlotItem,
)
from irony.models.service_agent import ServiceAgent
from irony.services.whatsapp import user_whatsapp_service
from irony.util import whatsapp_utils
import irony.services.whatsapp.interactive_message_service as interactive_message_service
import irony.services.whatsapp.text_message_service as text_message_service
from irony.config.logger import logger


async def get_orders_by_status_for_agent_locations(
    agent_mobile: str,
    ordered_statuses,
):
    response = FetchOrdersResponse()
    try:
        agent_data = await db.service_agent.find_one({"mobile": agent_mobile})
        if agent_data is None:
            raise Exception("Service agent not found")

        agent: ServiceAgent = ServiceAgent(**agent_data)

        if agent.service_location_ids is None:
            raise Exception("Service agent has no service locations")

        pipeline: List[Dict[str, Any]] = [
            {
                "$match": {
                    "order_status.0.status": {"$in": ordered_statuses},
                    "service_location_id": {"$in": agent.service_location_ids},
                }
            },
        ]
        orders = await db.order.aggregate(pipeline).to_list(None)

        if not orders:
            response.success = False
            response.error = "No orders found"
            return response.model_dump()

        response.body = setResponseBody(orders, ordered_statuses)
        response.success = True
        return response.model_dump(
            exclude={
                "body": {
                    "__all__": {
                        "orders": {
                            "__all__": {
                                "order_status",
                                "user",
                                "user_id",
                                "trigger_order_request_at",
                                "auto_alloted",
                            }
                        }
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"Error occurred in fetch orders: {e}", exc_info=True)
        response.success = False
        response.error = "Error occured in fetch orders"
        return response.model_dump()


async def get_orders_by_status_and_group_by_date_and_time_slot_for_agent_locations(
    agent_mobile: str,
    ordered_statuses,
):
    response = FetchOrdersResponse()
    try:
        agent_data = await db.service_agent.find_one({"mobile": agent_mobile})
        if agent_data is None:
            raise Exception("Service agent not found")

        agent: ServiceAgent = ServiceAgent(**agent_data)

        if agent.service_location_ids is None:
            raise Exception("Service agent has no service locations")

        pipeline: List[Dict[str, Any]] = [
            {
                "$match": {
                    "order_status.0.status": {"$in": ordered_statuses},
                    # "service_location_id": {"$in": agent.service_location_ids},
                }
            },
            {"$sort": {"pick_up_time.start": -1, "time_slot": 1}},
            {
                "$addFields": {
                    "latest_status": {"$arrayElemAt": ["$order_status", 0]},
                    "pick_up_date": {
                        "$dateToString": {
                            "format": "%d-%m-%Y",
                            "date": "$pick_up_time.start",
                        }
                    },
                }
            },
            {
                "$group": {
                    "_id": {
                        "latest_status": "$latest_status.status",
                        "pick_up_date": "$pick_up_date",
                        "time_slot": "$time_slot",
                    },
                    "orders": {"$push": "$$ROOT"},
                }
            },
            {
                "$sort": {
                    "_id.latest_status": 1,
                    "_id.pick_up_date": -1,
                    "_id.time_slot": 1,
                }
            },
        ]

        grouped_orders = await db.order.aggregate(pipeline).to_list(None)

        if not grouped_orders:
            response.success = False
            response.error = "No orders found"
            return response.model_dump()

        # return grouped_orders
        response.body = setGroupByResponseBody(grouped_orders, ordered_statuses)
        response.success = True
        return response

    except Exception as e:
        logger.error(f"Error occurred in fetch orders: {e}", exc_info=True)
        response.success = False
        response.error = "Error occured in fetch orders"
        return response.model_dump()


def setResponseBody(orders, ordered_statuses):
    logger.info(f"Orders: {orders}")
    response_dict: Dict[OrderStatusEnum, FetchOrdersResponseBodyItem] = {}
    # {
    #     "pending_pick_up": FetchOrdersResponseBodyItem(value="Pickup", orders=[]),
    #     "work_in_progress": FetchOrdersResponseBodyItem(
    #         value="Work In Progress", orders=[]
    #     ),
    #     "delivery_pending": FetchOrdersResponseBodyItem(value="Delivery", orders=[]),
    # }
    for order in orders:
        order = Order(**order)
        order_status = order.order_status[0].status
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
        if response_dict.get(order_status) is None:
            home_section_label = OrderStatusEnum.getHomeSectionLabel(order_status)
            response_dict[order_status] = FetchOrdersResponseBodyItem(
                key=order_status, label=home_section_label, orders=[order]
            )
        else:
            # TODO when i put model_dump() here, service_location_id = None is changing to service_location_id = 'None'. Why?
            response_dict[order_status].orders.append(order)

    respnse_body = [
        response_dict[status] for status in ordered_statuses if status in response_dict
    ]
    return respnse_body


def setGroupByResponseBody(grouped_orders, ordered_statuses):
    # logger.info(f"Orders: {grouped_orders}")
    # response_dict: Dict[OrderStatusEnum, FetchOrdersResponseBodyItem] = {}
    response_dict = {}
    # {
    #     "pending_pick_up": FetchOrdersResponseBodyItem(value="Pickup", orders=[]),
    #     "work_in_progress": FetchOrdersResponseBodyItem(
    #         value="Work In Progress", orders=[]
    #     ),
    #     "delivery_pending": FetchOrdersResponseBodyItem(value="Delivery", orders=[]),
    # }e
    for order_group in grouped_orders:
        if (
            order_group.get("_id") is None
            or order_group.get("_id").get("latest_status") is None
            or order_group.get("_id").get("pick_up_date") is None
            or order_group.get("_id").get("time_slot") is None
            or order_group.get("orders") is None
        ):
            continue

        if order_group.get("_id").get("latest_status") not in response_dict:
            response_dict[order_group.get("_id").get("latest_status")] = {}

        status_dict = response_dict[order_group.get("_id").get("latest_status")]

        if order_group.get("_id").get("pick_up_date") not in status_dict:
            status_dict[order_group.get("_id").get("pick_up_date")] = {}

        date_dict = status_dict[order_group.get("_id").get("pick_up_date")]

        if order_group.get("_id").get("time_slot") not in date_dict:
            date_dict[order_group.get("_id").get("time_slot")] = []

        slot_list = date_dict[order_group.get("_id").get("time_slot")]

        for order in order_group.get("orders"):
            order = Order(**order)
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
            slot_list.append(order)

    response_body = []
    for order_status in ordered_statuses:
        if order_status not in response_dict:
            continue
        status_obj = response_dict[order_status]
        label = OrderStatusEnum.getHomeSectionLabel(order_status)
        date_item_list: List[DateItem] = []
        for date in status_obj:
            date_obj = status_obj[date]
            time_slot_item_list: List[TimeSlotItem] = []
            for time_slot in date_obj:
                time_slot_item_list.append(
                    TimeSlotItem(time_slot=time_slot, orders=date_obj[time_slot])
                )
            date_item_list.append(DateItem(date=date, time_slots=time_slot_item_list))

        response_body.append(
            FetchOrdersResponseBodyItem1(
                key=order_status, label=label, dates=date_item_list
            )
        )

    return response_body

    respnse_body = [
        response_dict[status] for status in ordered_statuses if status in response_dict
    ]
    return response_dict


def setModel(order: Order):
    orderChunk = OrderChunk()
    if order is not None:
        orderChunk.order_id = str(order.id) if order.id is not None else None
        orderChunk.simple_id = order.simple_id
        orderChunk.clothes_count = str(order.count_range)
        if order.services is not None and len(order.services) > 0:
            orderChunk.service_name = order.services.__getitem__(0).service_name
        if order.pick_up_time is not None and order.pick_up_time.start is not None:
            orderChunk.pickup_time = order.pick_up_time.start.isoformat()
    return orderChunk
