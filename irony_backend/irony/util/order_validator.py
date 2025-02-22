from typing import Dict, List

from fastapi import HTTPException

from irony.db import db
from irony.models.order_item import OrderItem
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.prices import Prices
from irony.models.pyobjectid import PyObjectId
from irony.models.service_agent.vo.order_request_vo import CommonOrderRequest


# NOTE : this file is not used anywhere in the codebase.
class OrderValidator:
    @staticmethod
    async def validate_price(
        request: CommonOrderRequest, service_grouped_items: Dict[str, List[OrderItem]]
    ) -> None:
        if not request.items:
            return

        price = 0.0
        price_ids = [PyObjectId(item.price_id) for item in request.items]
        prices = await db.prices.find({"_id": {"$in": price_ids}}).to_list(None)
        prices = [Prices(**price) for price in prices]
        price_map = {str(price.id): price for price in prices}

        for item in request.items:
            await OrderValidator._validate_item_price(
                item, price_map, service_grouped_items
            )
            price += item.amount

        if request.total_price != price:
            raise HTTPException(status_code=400, detail="Price mismatch")

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> None:
        if (
            current_status not in OrderStatusEnum.__members__.values()
            or new_status not in OrderStatusEnum.__members__.values()
        ):
            raise HTTPException(status_code=400, detail="Invalid status provided")

        if current_status == new_status:
            raise HTTPException(
                status_code=400, detail="Current status and new status are same"
            )

        valid_transitions: Dict = {
            OrderStatusEnum.PICKUP_PENDING: [
                OrderStatusEnum.WORK_IN_PROGRESS,
                OrderStatusEnum.PICKUP_USER_NO_RESP,
                OrderStatusEnum.PICKUP_USER_REJECTED,
            ],
            OrderStatusEnum.WORK_IN_PROGRESS: [OrderStatusEnum.DELIVERY_PENDING],
            OrderStatusEnum.DELIVERY_PENDING: [OrderStatusEnum.DELIVERED],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from {current_status}",
            )

    @staticmethod
    async def _validate_item_price(
        item: OrderItem, price_map: Dict, service_grouped_items: Dict
    ) -> None:
        associated_service_id = price_map[item.price_id].service_id
        if associated_service_id not in service_grouped_items:
            service_grouped_items[associated_service_id] = []

        service_grouped_items[associated_service_id].append(item)

        if item and item.amount:
            if (item.amount / item.count) != price_map[item.price_id].price:
                raise HTTPException(
                    status_code=400, detail=f"Price mismatch for item: {item.price_id}"
                )
