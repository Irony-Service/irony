from contextlib import asynccontextmanager
from fastapi import FastAPI

from irony import cache
from irony.config import config
from irony.routers import users, whatsapp

# Initialize an empty dictionary to act as the cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event equivalent
    config.DB_CACHE = await cache.fetch_data_from_db(config.DB_CACHE)
    print("Data loaded into cache")

    # Yield control to the app
    yield

    # Shutdown event equivalent
    print("Application shutdown, you can clean up resources here")


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(whatsapp.router, prefix="/whatsapp")
app.include_router(users.router)
