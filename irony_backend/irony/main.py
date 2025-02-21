import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.file_lock import FileLockError, file_lock
from irony.routers import agent, ironman, users, whatsapp
from irony.scheduler import create_scheduler
from irony.util import background_process

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event equivalent
    config.DB_CACHE = await cache.fetch_data_from_db(config.DB_CACHE)
    logger.info("Data loaded into cache")

    scheduler = create_scheduler()
    scheduler.start()
    logger.info("All scheduler jobs started")

    try:
        yield
    finally:
        scheduler.shutdown()
    logger.info("Application shutdown, scheduler stopped")


app = FastAPI()

app.router.lifespan_context = lifespan

origins = ["http://localhost:3000"]
# origins = ["*"]
cookie_secure = False
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("User-Agent", "Unknown")
    request_url = request.url.path
    origin = request.headers.get("Origin", "No Origin Header")
    logger.info(
        f"Incoming request from IP: {client_ip}, User-Agent: {user_agent}, URL: {request_url}, Origin: {origin}"
    )
    response = await call_next(request)
    end_time = time.perf_counter()
    process_time = (end_time - start_time) * 1000
    logger.info(
        f"Request Time : Request: {request.method} {request.url.path} completed in {process_time:.4f} milliseconds"
    )
    return response


# @app.middleware("http")
# async def log_request_time(request: Request, call_next):
#     start_time = time.perf_counter()
#     client_ip = request.client.host if request.client else "Unknown"
#     user_agent = request.headers.get("User-Agent", "Unknown")
#     request_url = request.url.path
#     logger.info(
#         f"Incoming request from IP: {client_ip}, User-Agent: {user_agent}, URL: {request_url}"
#     )
#     response = await call_next(request)
#     end_time = time.perf_counter()
#     process_time = (end_time - start_time) * 1000
#     logger.info(
#         f"Requst Time : Request: {request.method} {request.url.path} completed in {process_time:.4f} milliseconds"
#     )
#     # response.headers["X-Process-Time"] = str(
#     #     process_time
#     # )  # Optional: Add timing info to the response
#     return response


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(whatsapp.router, prefix="/api/whatsapp")
app.include_router(users.router, prefix="/api/users")
app.include_router(ironman.router, prefix="/api/ironman")
app.include_router(agent.router, prefix="/api")
