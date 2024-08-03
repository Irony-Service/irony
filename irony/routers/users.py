from typing import List
from fastapi import APIRouter

router = APIRouter()

from irony.models.user import User
from ..db import get_users, create_user


@router.get("/users", response_model=List[User])
async def get_users():
    users = await get_users()
    return users


@router.post("/users", response_model=User)
async def create_user(user: User):
    created_user = await create_user(user)
    return created_user
