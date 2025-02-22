from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from irony.models import service
from irony.models.common_model import CommonModel
from irony.models.common_response import CommonReponse
from irony.models.service import Service
from irony.models.prices import Prices


# class ServicePrices(CommonModel):
#     service_id: Optional[str] = None
#     prices: Optional[List[Prices]] = None


class ServicePrices(BaseModel):
    service: Service
    prices: Optional[List[Prices]] = None


class PricesResponseVo(CommonReponse):
    data: Optional[Dict[str, List[ServicePrices]]] = None
    pass
