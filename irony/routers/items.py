from typing import List
from fastapi import APIRouter

router = APIRouter()

from ..models.item import Item

@router.get("/items")
async def get_items():
   return [Item('abc', 'TITSle', 'BooooooooYeah')]