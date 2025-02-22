from typing import Any, Dict, List

from fastapi import HTTPException

from irony.config import config
from irony.config.logger import logger
from irony.db import db
from irony.models.prices import Prices
from irony.models.service import Service
from irony.models.service_agent.service_agent import ServiceAgent
from irony.models.service_agent.vo.prices_response_vo import (
    PricesResponseVo,
    ServicePrices,
)
from irony.util import pipelines


async def get_service_prices_for_locations(current_user: str) -> PricesResponseVo:
    """Get service prices for all locations assigned to an agent.

    Args:
        current_user (str): Mobile number of the current user/agent.

    Returns:
        PricesResponseVo: Response containing service prices grouped by location.

    Raises:
        HTTPException: If agent validation fails or there's an error fetching prices.
    """
    try:
        response = PricesResponseVo()

        services: Dict[str, Service] = {
            str(service.id): service
            for service in config.DB_CACHE.get("services", {}).values()
        }

        # Validate agent
        agent = await _validate_agent(current_user)

        # Get prices from database
        pipeline: List[Dict[str, Any]] = pipelines.get_pipeline_service_prices_for_locations(agent.service_location_ids)  # type: ignore

        prices_groups = await db.prices.aggregate(pipeline=pipeline).to_list(None)

        if not prices_groups:
            response.message = "No orders found"
            return response

        # Group prices by location and service
        service_location_service_prices = _group_prices_by_location_and_service(
            prices_groups
        )

        # Build response body
        response.data = _build_response_body(service_location_service_prices, services)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in get_service_prices_for_locations: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching service prices",
        ) from e


async def _validate_agent(current_user):
    """Validate service agent exists and has assigned service locations.

    Args:
        current_user (str): Mobile number of the agent to validate.

    Returns:
        ServiceAgent: Validated service agent object.

    Raises:
        HTTPException: If agent not found or has no service locations.
    """
    agent_doc = await db.service_agent.find_one({"mobile": current_user})
    if not agent_doc:
        raise HTTPException(status_code=404, detail="Service agent not found")

    agent: ServiceAgent = ServiceAgent(**agent_doc)

    if agent.service_location_ids is None:
        raise HTTPException(
            status_code=400, detail="Service agent has no service locations"
        )

    return agent


def _group_prices_by_location_and_service(
    prices_groups: List[Dict],
) -> Dict[str, Dict[str, List[Prices]]]:
    """Group prices by location and service IDs.

    Args:
        prices_groups (List[Dict]): Raw price data from database aggregation.

    Returns:
        Dict[str, Dict[str, List[Prices]]]: Grouped prices by location and service.
    """
    service_location_service_prices: Dict[str, Dict[str, List[Prices]]] = {}

    for price_group in prices_groups:
        service_location_id = str(price_group.get("_id", {}).get("service_location_id"))
        service_id = str(price_group.get("_id", {}).get("service_id"))

        if service_location_id not in service_location_service_prices:
            service_location_service_prices[service_location_id] = {}
        service_location_service_prices[service_location_id][service_id] = [
            Prices(**price_item) for price_item in price_group.get("prices", [])
        ]

    return service_location_service_prices


def _build_response_body(
    service_location_service_prices: Dict[str, Dict[str, List[Prices]]],
    services: Dict[str, Service],
) -> Dict[str, List[ServicePrices]]:
    """Build response body with sorted service prices.

    Args:
        service_location_service_prices (Dict[str, Dict[str, List[Prices]]]): Grouped prices by location and service.
        services (Dict[str, Service]): Dictionary of services.

    Returns:
        Dict[str, List[ServicePrices]]: Response body with sorted service prices.
    """
    response_body: Dict[str, List[ServicePrices]] = {}

    for service_location_id, service_prices in service_location_service_prices.items():
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

    return response_body
