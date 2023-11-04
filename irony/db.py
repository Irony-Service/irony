from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient
import config
client = AsyncIOMotorClient(config.DATABASE_CONNECTION)
db = client['irony']

# Pydantic models
from .models.user import User

# DB methods
async def get_users():
    users = await db.users.find().to_list(100)
    return users

async def create_user(user: User):
    user = jsonable_encoder(user)
    new_user = await db.users.insert_one(user)
    return new_user

# etc...