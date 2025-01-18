from typing import Any, Dict, List, Optional
from irony.models import service
from irony.models.common_model import CommonModel
from irony.models.service import Service
from irony.models.service_agent.prices import Prices


# class ServicePrices(CommonModel):
#     service_id: Optional[str] = None
#     prices: Optional[List[Prices]] = None


class ServicePrices(CommonModel):
    service: Service
    prices: Optional[List[Prices]] = None


class PricesResponseVo(CommonModel):
    success: Optional[bool] = None
    body: Optional[Dict[str, List[ServicePrices]]] = None
    error: Optional[str] = None
    pass
