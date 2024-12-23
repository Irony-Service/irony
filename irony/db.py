from typing import Any, Dict, List
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from pymongo import ReplaceOne
import certifi
from irony.config import config
from irony.config.logger import logger
from pymongo.errors import PyMongoError

from motor.core import AgnosticClient, AgnosticDatabase

client: AgnosticClient = AsyncIOMotorClient(
    config.DATABASE_CONNECTION, tlsCAFile=certifi.where()
)
db: AgnosticDatabase = client["irony"]

# Pydantic models
from .models.user import User


# DB methods
async def replace_documents_in_transaction(
    collection_name: str, replacements: List[Any]
):
    # Prepare bulk operations list
    operations: list = []

    for replacement in replacements:
        # Filter criteria for each document to be replaced
        filter_criteria = {"_id": ObjectId(replacement["_id"])}

        # Create a ReplaceOne operation and add it to the operations list
        operations.append(ReplaceOne(filter_criteria, replacement))

    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                # Execute all replacements as a bulk operation within the transaction
                result = await db[collection_name].bulk_write(
                    operations, session=session
                )
                logger.info(
                    f"Matched count: {result.matched_count}, Modified count: {result.modified_count}"
                )
            except PyMongoError as e:
                logger.error(
                    f"Transaction aborted due to an error",
                    exc_info=True,
                    stack_info=True,
                )
                await session.abort_transaction()


async def get_users():
    users = await db.users.find().to_list(100)
    return users


async def create_user(user: User):
    user = jsonable_encoder(user)
    new_user = await db.users.insert_one(user)
    return new_user


# etc...
