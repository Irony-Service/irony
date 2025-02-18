from fastapi import HTTPException

from irony.config.logger import logger
from irony.db import db
from irony.models.order import Order
from irony.models.pyobjectid import PyObjectId
from irony.models.service_agent.vo.fetch_order_details_vo import (
    FetchOrderDetailsResponse,
    FetchOrderDetailsResponsebody,
)
from irony.models.user import User


async def fetch_order_details(order_id: str) -> FetchOrderDetailsResponse:
    """Fetch detailed information for a specific order including user details.

    Args:
        order_id (str): The unique identifier of the order to fetch

    Returns:
        FetchOrderDetailsResponse: Response containing detailed order and user information

    Raises:
        HTTPException:
            - 404 if order not found
            - 500 for internal server errors
    """
    try:
        response = FetchOrderDetailsResponse()

        order_doc = await db.order.find_one({"_id": PyObjectId(order_id)})
        if not order_doc:
            raise HTTPException(status_code=404, detail="Order not found")
        order: Order = Order(**order_doc)

        user_doc = await db.user.find_one({"wa_id": order.user_wa_id})

        response.body = _map_order_to_response(order, user_doc)

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in fetch_order_details: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching order details"
        ) from e


def _map_order_to_response(order: Order, user):
    """Map order and user data to a formatted response body.

    Args:
        order (Order): Order model instance containing order details
        user (dict): User document containing associated user information

    Returns:
        FetchOrderDetailsResponsebody: Formatted response containing order and user details

    Notes:
        - Formats location as either nickname or coordinates
        - Converts datetime objects to ISO format strings
        - Includes user details if available
        - Extracts first status from order status history
    """
    responsebody = FetchOrderDetailsResponsebody()
    responsebody.order_id = str(order.id)
    responsebody.simple_id = order.simple_id
    responsebody.count_range = order.count_range
    responsebody.services = order.services
    responsebody.service_location_id = str(order.service_location_id)
    if order.location:
        if order.location.nickname:
            responsebody.location = order.location.nickname
        elif order.location.location and order.location.location.coordinates:
            responsebody.location = (
                str(order.location.location.coordinates[0])
                + ","
                + str(order.location.location.coordinates[1])
            )

    if order.pickup_date_time:
        if order.pickup_date_time.start:
            responsebody.pickup_time_start = order.pickup_date_time.start.isoformat()
        if order.pickup_date_time.end:
            responsebody.pickup_time_end = order.pickup_date_time.end.isoformat()

    responsebody.time_slot = order.time_slot

    if order.order_status:
        responsebody.status = order.order_status[0].status

    if user:
        user = User(**user)
        responsebody.name = user.name
        responsebody.phone_number = user.wa_id

    return responsebody
