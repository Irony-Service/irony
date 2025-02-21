import fcntl
import os
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.routers import agent, ironman, users, whatsapp
from irony.util import background_process

# Initialize the scheduler


async def execute_all_background_tasks():
    """Execute all background tasks in sequence"""
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
        try:
            # Attempt non-blocking exclusive lock
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Run batch job if lock acquired
        except BlockingIOError:
            logger.warning("Another instance of the batch job is already running")
            os.close(fd)
            return
    except OSError as e:
        logger.error(f"Failed to open lock file: {e}")
        return

    await background_process.reset_daily_config()
    await background_process.send_pending_order_requests()
    await background_process.send_ironman_delivery_schedule()
    await background_process.send_ironman_work_schedule()
    await background_process.send_ironman_pending_work_schedule()
    await background_process.create_timeslot_volume_record()
    await background_process.create_order_requests()
    await background_process.reassign_missed_orders()


LOCK_FILE = os.path.join(os.path.dirname(__file__), "locks", "batch.lock")

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.DB_CACHE = await cache.fetch_data_from_db(config.DB_CACHE)
    logger.info("Data loaded into cache")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(execute_all_background_tasks, CronTrigger(minute="*/1"))
    scheduler.start()
    logger.info("Scheduler started on 1 worker")
    try:
        yield
    finally:
        pass
    logger.info("Application shutdown, you can clean up resources here")


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
