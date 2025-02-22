import asyncio
from datetime import datetime
from typing import Any, Dict, List
import httpx
from fastapi import HTTPException
from irony.db import db
from irony.models.order import Order
from irony.config.logger import logger
from irony.config import config

async def get_optimized_route(coordinates: List[str]) -> Dict[Any, Any]:
    """Get optimized route indices from OSRM service"""
    try:
        # Convert coordinates list to OSRM format
        coords_string = ";".join(coordinates)
        url = f"{config.OSRM_URL}/trip/v1/driving/{coords_string}"
        
        params = {
            "roundtrip": "true",
            "source": "first"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)

        
        if response.status_code == 400:
            data = response.json()
            if data["code"] ==  "NoTrips":
                logger.error(f"OSRM service error: {data['message']}")
                raise HTTPException(status_code=400, detail="No route found")     
        elif response.status_code != 200:
            logger.error(f"OSRM service error: {response.text}")
            raise HTTPException(status_code=500, detail="Route optimization service error")

        data = response.json()
        # Extract waypoint indices in optimized order
        route_legs = data.get("trips", [0])[0].get("legs", [])
        distance_list = [leg.get("distance") for leg in route_legs]
        
        return {"waypoints": [waypoint["waypoint_index"] for waypoint in data.get("waypoints", [])], "distances": distance_list}
   
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Error making request to OSRM service: {e}")
        raise HTTPException(status_code=503, detail="Route optimization service unavailable")
    except Exception as e:
        logger.error(f"Error in route optimization: {e}")
        raise HTTPException(status_code=500, detail="Route optimization failed")

async def route_sort_orders(orders: List[Order]) -> List[Order]:
    """
    Get optimized route and distances for orders
    Returns a dict containing:
    - sorted_orders: List of orders in optimized sequence
    - distances: List of distances between consecutive points
    """
    try:
        # Extract coordinates from orders
        coordinates = []
        for order in orders:
            if order.location and order.location.location:
                coordinates.append(order.location.location.to_coordinates_string())

        if not coordinates:
            return orders

        # Get optimized route data
        route_data = await get_optimized_route(coordinates)
        
        # Create new sorted list based on waypoint indices
        sorted_orders: List[Order] = [None] * len(orders)  # type: ignore
        for orig_pos, new_pos in enumerate(route_data["waypoints"]):
            order: Order = orders[orig_pos] # type: ignore
            if new_pos > 0:
                order.distance_from_previous_stop = route_data["distances"][new_pos-1]
            sorted_orders[new_pos] = order

        return sorted_orders

    except HTTPException as e:
        handle_route_error(orders, e)
        return orders
    except Exception as e:
        logger.error(f"Error in route_sort_orders: {e}")
        # Return original order if sorting fails
        return orders
    

def handle_route_error(order_list_for_date_and_slot, e):
    if e.status_code == 400:
        if e.detail == "No route found":
            asyncio.create_task(
                            db.route_exceptions.insert_one({
                                "status_code": e.status_code,
                                "order_ids": [order.id for order in order_list_for_date_and_slot],
                                "details": e.detail,
                                "created_at": datetime.now()
                            })
                        )
            logger.error(f"No route found for orders: {order_list_for_date_and_slot}")