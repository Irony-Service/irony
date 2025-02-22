from enum import Enum
from irony.models.pyobjectid import PyObjectId
from pydantic import BaseModel


class DeliveryAgent(BaseModel):
    id: PyObjectId
    name: str
    phone: str
    age: str
    vehicle_type: int
    vehicle_sub_type: str
    vehicle_name: str
    vehicle_number_plate: str
    rating: float


class VehicleTypeEnum(int, Enum):
    TWO = 2
    THREE = 3
    FOUR = 4


class VehicleSubTypeEnum(str, Enum):
    SCOOTY = "SCOOTY"
    BIKE = "BIKE"
    ELECTRIC_AUTO = "ELECTRIC_AUTO"
    VAN = "VAN"
