from typing import List
from fastapi import APIRouter


from irony.models.user import User
from ..db import get_users, create_user

router = APIRouter()


@router.get("/home")
async def get_users(agent_id: int):

    pass


@router.post("/users", response_model=User)
async def create_user(user: User):
    created_user = await create_user(user)
    return created_user
