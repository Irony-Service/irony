from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

class User(BaseModel):
    id: ObjectId
    name: str
    phone_number: str
    created_on: datetime