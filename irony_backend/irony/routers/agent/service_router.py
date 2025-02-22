from fastapi import APIRouter, Depends

from irony.services.agent import service_service
from irony.util import auth

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/prices")
async def get_service_prices_for_service_locations(
    current_user: str = Depends(auth.get_current_user),
):
    """
    Get service prices for available service locations.

    Args:
        current_user (str): Authenticated user ID

    Returns:
        dict: Service prices by location
    """
    return await service_service.get_service_prices_for_locations(current_user)
