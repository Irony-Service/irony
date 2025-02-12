from typing import Any, List
from irony.models.pyobjectid import PyObjectId
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReplaceOne, InsertOne, UpdateOne, DeleteOne, UpdateMany, DeleteMany
import certifi
from pymongo.errors import PyMongoError
from motor.core import AgnosticClient, AgnosticDatabase

from irony.config import config
from irony.config.logger import logger

# Pydantic models
from .models.user import User

client: AgnosticClient = AsyncIOMotorClient(
    config.DATABASE_CONNECTION, tlsCAFile=certifi.where()
)
db: AgnosticDatabase = client["irony"]


# DB methods
async def replace_documents_in_transaction(
    collection_name: str, replacements: List[Any], upsert: bool = False
):
    # Prepare bulk operations list
    operations: list = []

    for replacement in replacements:
        # Filter criteria for each document to be replaced
        filter_criteria = {"_id": PyObjectId(replacement["_id"])}

        # Create a ReplaceOne operation and add it to the operations list
        operations.append(ReplaceOne(filter_criteria, replacement, upsert=upsert))

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


async def bulk_insert_documents(
    collection_name: str, documents: List[Any]
) -> List[PyObjectId]:
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                result = await db[collection_name].insert_many(
                    documents, session=session
                )
                logger.info(
                    f"Successfully inserted {len(result.inserted_ids)} documents"
                )
                return result.inserted_ids
            except PyMongoError as e:
                logger.error(
                    f"Failed to bulk insert documents: {str(e)}",
                    exc_info=True,
                    stack_info=True,
                )
                await session.abort_transaction()
                raise


async def bulk_write_operations(collection_name: str, operations: List[Any]) -> dict:
    """
    Perform bulk write operations (insert, update, delete) in a single transaction.
    operations: List of PyMongo operations (InsertOne, UpdateOne, DeleteOne, etc.)
    """
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                result = await db[collection_name].bulk_write(
                    operations,
                    session=session,
                    ordered=False,  # Allow parallel execution
                )
                logger.info(
                    f"Bulk write results - "
                    f"Inserted: {result.inserted_count}, "
                    f"Modified: {result.modified_count}, "
                    f"Deleted: {result.deleted_count}"
                )
                return {
                    "inserted_count": result.inserted_count,
                    "modified_count": result.modified_count,
                    "deleted_count": result.deleted_count,
                    "upserted_count": result.upserted_count,
                    "upserted_ids": result.upserted_ids,
                }
            except PyMongoError as e:
                logger.error(
                    f"Bulk write operation failed: {str(e)}",
                    exc_info=True,
                    stack_info=True,
                )
                await session.abort_transaction()
                raise


# etc...
