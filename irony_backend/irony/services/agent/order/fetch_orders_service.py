import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from irony.config import config
from irony.config.logger import logger
from irony.db import db
from irony.models.order import Order
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.order_vo import OrderVo
from irony.models.service_agent.service_agent import ServiceAgent
from irony.models.service_agent.vo.fetch_orders_response import (
    DateItem,
    FetchOrdersResponse,
    FetchOrdersResponseDataItem,
    TimeSlotItem,
)
from irony.util import pipelines, route, utils


# Route : 1
async def get_orders_group_by_status_and_date_and_time_slot(
    agent_mobile: str,
    ordered_statuses: List[OrderStatusEnum],
) -> FetchOrdersResponse:
    """Fetch and group orders by status, date, and time slot.

    Args:
        agent_mobile (str): Mobile number of the service agent
        ordered_statuses (List[OrderStatusEnum]): List of order statuses to filter by

    Returns:
        FetchOrdersResponse: Response containing grouped orders

    Raises:
        HTTPException: If agent not found or other errors occur
    """
    try:
        response = FetchOrdersResponse()

        agent: ServiceAgent = await _retrieve_agent_by_mobile_with_service_location(
            agent_mobile
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_orders_group_by_status_and_date_and_time_slot_for_service_location_ids(
                agent.service_location_ids,  # type: ignore
                ordered_statuses,
            )
        )
        grouped_orders = await db.order.aggregate(pipeline).to_list(None)

        if not grouped_orders:
            response.message = "No orders founrd"
            return response

        grouped_dict = _group_by_status_and_date_and_time_slot(grouped_orders)

        response.data = _construct_fetch_order_response(grouped_dict, ordered_statuses)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unknown Error occurred in fetch orders: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error occurred in fetch orders"
        ) from e


def _group_by_status_and_date_and_time_slot(grouped_orders) -> Dict:
    """Group orders by their status, date, and time slot.

    Args:
        grouped_orders (List[Dict]): Raw grouped orders from database

    Returns:
        Dict: Nested dictionary with structure {status: {date: {time_slot: [orders]}}}
    """
    grouped_dict: Dict = {}

    for order_group in grouped_orders:
        if (
            order_group.get("_id") is None
            or order_group.get("_id").get("latest_status") is None
            or order_group.get("_id").get("pick_up_date") is None
            or order_group.get("_id").get("time_slot") is None
            or order_group.get("orders") is None
        ):
            continue

        _add_order_to_grouped_dict_by_status_and_date_and_time_slot(
            grouped_dict, order_group
        )

    return grouped_dict


def _add_order_to_grouped_dict_by_status_and_date_and_time_slot(
    response_dict, order_group
):
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


# Route : 2
async def get_orders_group_by_date_and_time_slot_routable(
    agent_mobile: str,
    ordered_statuses: List[OrderStatusEnum],
    route_required: bool = False,
) -> FetchOrdersResponse:
    """Fetch and group orders with optional route optimization.

    Args:
        agent_mobile (str): Mobile number of the service agent
        ordered_statuses (List[OrderStatusEnum]): List of order statuses to filter by
        route_required (bool, optional): Whether to calculate optimal route. Defaults to False.

    Returns:
        FetchOrdersResponse: Response containing grouped and optionally routed orders

    Raises:
        HTTPException: If agent not found or routing fails
    """
    try:
        response = FetchOrdersResponse()
        agent: ServiceAgent = await _retrieve_agent_by_mobile_with_service_location(
            agent_mobile
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_orders_group_by_date_and_time_slot_for_service_location_ids(
                [str(location_id) for location_id in agent.service_location_ids],  # type: ignore
                ordered_statuses,
            )
        )
        grouped_orders = await db.order.aggregate(pipeline).to_list(None)

        if not grouped_orders:
            response.message = "No orders found"
            return response

        grouped_dict = await _group_by_date_and_time_slot_routable(
            grouped_orders, route_required
        )
        response.data = _construct_fetch_order_response(
            grouped_dict, ordered_statuses, ["Pickup / Delivery"], True
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_orders_for_statuses_group_by_date_and_time_slot_for_agent_locations: %s",
            str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching grouped orders",
        ) from e


async def _group_by_date_and_time_slot_routable(
    grouped_orders,
    route_required=False,
) -> Dict:
    """Group orders by date and time slot with optional routing.

    Args:
        grouped_orders (List[Dict]): Raw grouped orders from database
        route_required (bool, optional): Whether to calculate optimal route. Defaults to False.

    Returns:
        Dict: Nested dictionary with structure {date: {time_slot: [orders]}}
    """
    grouped_dict: Dict = {}

    for order_group in grouped_orders:
        if (
            order_group.get("_id") is None
            or not order_group.get("_id").get("pick_up_date")
            or not order_group.get("_id").get("time_slot")
            or not order_group.get("orders")
        ):
            continue

        date = order_group.get("_id").get("pick_up_date")
        time_slot = order_group.get("_id").get("time_slot")
        orders_list_for_date_and_slot = order_group.get("orders")

        can_route = await _add_orders_to_grouped_dict_by_date_and_time_slot(
            grouped_dict, date, time_slot, orders_list_for_date_and_slot, route_required
        )

        grouped_dict[date][time_slot] = await _sort_orders_if_routable(
            grouped_dict[date][time_slot], can_route
        )

    return grouped_dict


async def _add_orders_to_grouped_dict_by_date_and_time_slot(
    response_dict: Dict,
    date: datetime,
    time_slot: str,
    input_orders_list_for_date_and_slot: List,
    route_required: bool,
) -> bool:
    """Add orders to grouped dictionary and determine if routing is needed.

    Args:
        response_dict (Dict): Dictionary to add orders to
        date (datetime): Order date
        time_slot (str): Time slot identifier
        input_orders_list_for_date_and_slot (List): List of orders to process
        route_required (bool): Whether routing is required

    Returns:
        bool: True if orders can be routed, False otherwise
    """
    if date not in response_dict:
        response_dict[date] = {}

    if time_slot not in response_dict[date]:
        response_dict[date][time_slot] = []

    delivery_time_gap = (
        config.DB_CACHE.get("config", {})
        .get("delivery_schedule_time_gap", {})
        .get("value", 60)
    )
    cuttoff_time = datetime.now() + timedelta(minutes=delivery_time_gap)

    output_orders_list_for_date_and_slot: List[Order] = []
    can_route = _populate_order_list(
        input_orders_list_for_date_and_slot,
        route_required,
        cuttoff_time,
        output_orders_list_for_date_and_slot,
    )

    response_dict[date][time_slot] = output_orders_list_for_date_and_slot
    return can_route


# Route : 3
async def get_orders_for_delivery_with_route(
    agent_mobile: str,
    ordered_statuses: List[OrderStatusEnum],
) -> FetchOrdersResponse:
    """Fetch orders for delivery and optimize route.

    Args:
        agent_mobile (str): Mobile number of the service agent
        ordered_statuses (List[OrderStatusEnum]): List of order statuses to filter by

    Returns:
        FetchOrdersResponse: Response containing delivery orders with optimized route

    Raises:
        HTTPException: If agent not found or routing fails
    """
    try:
        response = FetchOrdersResponse()
        agent: ServiceAgent = await _retrieve_agent_by_mobile_with_service_location(
            agent_mobile
        )

        pipeline: List[Dict[str, Any]] = (
            pipelines.get_pipeline_orders_by_status_for_service_location_ids(
                [str(location_id) for location_id in agent.service_location_ids],  # type: ignore
                ordered_statuses,
            )
        )

        delivery_orders = await db.order.aggregate(pipeline).to_list(None)

        if not delivery_orders:
            response.message = "No orders found"
            return response

        response_dict = await _get_response_dict_for_delivery_with_route(
            delivery_orders
        )

        response.data = _construct_fetch_order_response(
            response_dict, ordered_statuses, ["Pickup / Delivery"], True
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_orders_for_delivery_with_route: %s",
            str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching delivery route",
        ) from e


async def _get_response_dict_for_delivery_with_route(orders) -> Dict:
    """Construct response dictionary for delivery orders with route optimization.

    Args:
        orders (List[Dict]): List of delivery orders

    Returns:
        Dict: Response dictionary with optimized routes
    """
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    response_dict: Dict = {now: {}}

    delivery_time_gap = (
        config.DB_CACHE.get("config", {})
        .get("delivery_schedule_time_gap", {})
        .get("value", 60)
    )
    cuttoff_time = datetime.now() + timedelta(minutes=delivery_time_gap)

    order_list_for_date_and_slot: List[Order] = []
    can_route = _populate_order_list(
        orders,
        True,
        cuttoff_time,
        order_list_for_date_and_slot,
    )

    await _sort_orders_if_routable(order_list_for_date_and_slot, can_route)

    response_dict[now]["Routes"] = order_list_for_date_and_slot

    return response_dict


# Util functions
def _construct_fetch_order_response(
    grouped_dict: Dict,
    ordered_statuses: List[OrderStatusEnum],
    labels: Optional[List[str]] = None,
    single_status_group: bool = False,
) -> List[FetchOrdersResponseDataItem]:
    """Construct the final response from grouped orders.

    Args:
        grouped_dict (Dict): Grouped orders dictionary
        ordered_statuses (List[OrderStatusEnum]): List of order statuses
        labels (Optional[List[str]], optional): Custom labels for status groups. Defaults to None.
        single_status_group (bool, optional): Whether to combine all statuses. Defaults to False.

    Returns:
        List[FetchOrdersResponseDataItem]: Formatted response items

    Raises:
        ValueError: If labels don't match status count
    """
    response_body: List[FetchOrdersResponseDataItem] = []

    if single_status_group:
        key = "_AND_".join(ordered_statuses)
        if not labels:
            labels = [
                "/".join(
                    [
                        OrderStatusEnum.getHomeSectionLabel(order_status)
                        for order_status in ordered_statuses
                    ]
                )
            ]
        elif len(labels) != 1:
            raise ValueError("Labels should be provided for single status group")

        date_item_list = _construct_date_item_list(grouped_dict)
        response_body.append(
            FetchOrdersResponseDataItem(key=key, label=labels[0], dates=date_item_list)
        )

    else:
        if labels and len(labels) != len(ordered_statuses):
            raise ValueError("Labels if provided, should be provided for each status")
        for i, order_status in enumerate(ordered_statuses):
            if order_status not in grouped_dict:
                continue
            status_dict = grouped_dict[order_status]
            if labels:
                label = labels[i]
            else:
                label = OrderStatusEnum.getHomeSectionLabel(order_status)

            date_item_list = _construct_date_item_list(status_dict)
            response_body.append(
                FetchOrdersResponseDataItem(
                    key=order_status, label=label, dates=date_item_list
                )
            )

    return response_body


def _construct_date_item_list(status_dict) -> List[DateItem]:
    """Construct a list of DateItem objects from status dictionary.

    Args:
        status_dict (Dict): Dictionary of orders grouped by date and time slot

    Returns:
        List[DateItem]: List of DateItem objects
    """
    date_item_list: List[DateItem] = []
    return _populate_date_item_list(status_dict, date_item_list)


def _populate_date_item_list(status_dict, date_item_list) -> List[DateItem]:
    """Populate a list of DateItem objects from status dictionary.

    Args:
        status_dict (Dict): Dictionary of orders grouped by date and time slot
        date_item_list (List[DateItem]): List to populate with DateItem objects

    Returns:
        List[DateItem]: Populated list of DateItem objects
    """
    for date in status_dict:
        date_dict = status_dict[date]
        time_slot_item_list: List[TimeSlotItem] = []
        for time_slot in date_dict:
            time_slot_item_list.append(
                TimeSlotItem(time_slot=time_slot, orders=date_dict[time_slot])
            )
        date_item_list.append(DateItem(date=date, time_slots=time_slot_item_list))

    return date_item_list


def _populate_order_list(
    input_orders_list_for_date_and_slot,
    route_required,
    cuttoff_time,
    output_orders_list_for_date_and_slot,
) -> bool:
    """Populate the order list and determine if routing is needed.

    Args:
        input_orders_list_for_date_and_slot (List[Dict]): List of orders to process
        route_required (bool): Whether routing is required
        cuttoff_time (datetime): Cutoff time for routing
        output_orders_list_for_date_and_slot (List[Order]): List to populate with orders

    Returns:
        bool: True if orders can be routed, False otherwise
    """
    can_route = False
    for order in input_orders_list_for_date_and_slot:
        order = OrderVo(**order)

        if (
            route_required
            and not can_route
            and order.pickup_date_time
            and order.pickup_date_time.start
            and order.pickup_date_time.start < cuttoff_time
        ):
            can_route = True

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

        if (
            not order.order_status
            or not isinstance(order.order_status, list)
            or not len(order.order_status) > 0
        ):
            continue

        status = order.order_status.__getitem__(0).status
        order.delivery_type = OrderStatusEnum.getDeliveryType(status)
        order.maps_link = utils.get_maps_link(order.location)  # type: ignore

        output_orders_list_for_date_and_slot.append(order)
    return can_route


async def _sort_orders_if_routable(
    order_list_for_date_and_slot: List[Order], can_route: bool
) -> List[Order]:
    """Sort orders using route optimization if possible.

    Args:
        order_list_for_date_and_slot (List[Order]): Orders to sort
        can_route (bool): Whether routing is possible

    Returns:
        List[Order]: Sorted orders, either by route or original order

    Raises:
        HTTPException: If routing fails
    """
    if can_route:
        try:
            order_list_for_date_and_slot = await route.route_sort_orders(
                order_list_for_date_and_slot
            )
            logger.info("Route sorted orders: %s", order_list_for_date_and_slot)
        except HTTPException as e:
            _handle_route_error(order_list_for_date_and_slot, e)
    return order_list_for_date_and_slot


def _handle_route_error(
    order_list_for_date_and_slot: List[Order], e: HTTPException
) -> None:
    """Handle errors that occur during route optimization.

    Args:
        order_list_for_date_and_slot (List[Order]): Orders that failed routing
        e (HTTPException): The exception that occurred

    Notes:
        Logs error and creates exception record in database
    """
    if e.status_code == 400 and e.detail == "No route found":
        order_ids = [order.id for order in order_list_for_date_and_slot]
        asyncio.create_task(
            db.route_exceptions.insert_one(
                {
                    "status_code": e.status_code,
                    "order_ids": order_ids,
                    "details": e.detail,
                    "created_at": datetime.now(),
                }
            )
        )
        logger.error("No route found for orders: %s", str(order_ids))


async def _retrieve_agent_by_mobile_with_service_location(
    agent_mobile: str,
) -> ServiceAgent:
    """Retrieve agent and verify they have service locations.

    Args:
        agent_mobile (str): Mobile number of the service agent

    Returns:
        ServiceAgent: Agent details with service locations

    Raises:
        HTTPException: If agent not found or has no service locations
    """
    agent = await _get_agent_by_mobile(agent_mobile)
    if agent.service_location_ids is None:
        raise HTTPException(
            status_code=400, detail="Service agent has no service locations"
        )
    return agent


async def _get_agent_by_mobile(agent_mobile) -> ServiceAgent:
    """Retrieve agent details by mobile number.

    Args:
        agent_mobile (str): Mobile number of the service agent

    Returns:
        ServiceAgent: Agent details

    Raises:
        HTTPException: If agent not found
    """
    agent_data = await db.service_agent.find_one({"mobile": agent_mobile})
    if agent_data is None:
        raise HTTPException(status_code=404, detail="Service agent not found")

    return ServiceAgent(**agent_data)
