from typing import Optional
from pydantic import BaseModel

from irony.models.service_location import ServiceLocation
from irony.models.timeslot_volume import TimeslotVolume
from irony.models.common_model import shared_config



class TimeslotVolumePlus(TimeslotVolume):
    service_location: Optional[ServiceLocation] = None
    model_config = shared_config
