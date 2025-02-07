from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi.middleware.cors import CORSMiddleware

from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.routers import users, whatsapp, ironman
from irony.util import background_process

# Initialize the scheduler
scheduler = AsyncIOScheduler()

# Add the job to the scheduler
# TODO add this back when you want to send ironman_request
# scheduler.add_job(
#     background_process.send_pending_order_requests, CronTrigger(minute="*/1")
# )

scheduler.add_job(
    background_process.send_ironman_delivery_schedule, CronTrigger(minute="*/1")
)

# scheduler.add_job(
#     background_process.send_ironman_work_schedule, CronTrigger(minute="*/2")
# )

# scheduler.add_job(
#     background_process.send_ironman_pending_work_schedule, CronTrigger(minute="*/1")
# )
# scheduler.add_job(
#     background_process.create_timeslot_volume_record,
#     CronTrigger(hour=0, minute=0),  # This triggers at 12:00 AM every day
# )

# scheduler.add_job(background_process.create_order_requests, CronTrigger(minute="*/1"))

# scheduler.add_job(background_process.reassign_missed_orders, CronTrigger(minute="*/1"))


# Runs every 1 minute

# scheduler.add_job(
#     background_process.send_ironman_request, CronTrigger(minute="*/1")
# )  # Runs every 1 minute


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event equivalent
    config.DB_CACHE = await cache.fetch_data_from_db(config.DB_CACHE)
    logger.info("Data loaded into cache")
    # scheduler.start()
    # await background_process.send_pending_order_requests()
    logger.info("Scheduler started")
    # Yield control to the app
    try:
        yield
    finally:
        # Shutdown the scheduler
        # scheduler.shutdown()
        pass
    # Shutdown event equivalent
    logger.info("Application shutdown, you can clean up resources here")


app = FastAPI()

app.router.lifespan_context = lifespan


# origins = [
#     "http://localhost:3000",
#     "http://0.0.0.0:3000",
#     "http://127.0.0.1:3000",
#     "http://localhost:3001",
#     "http://0.0.0.0:3001",
#     "http://127.0.0.1:3001",
#     "http://localhost:8000",
#     "http://0.0.0.0:8000",
#     "http://127.0.0.1:8000",
#     "::1:8000",
#     "http://frontend:3000",
#     "http://172.18.0.0/16",  # Allow all IPs in the Docker network (adjust subnet if needed)
#     "http://192.168.1.47:3000",
#     "http://78446487bed8:3000",
# ]
origins = ["*"]

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


app.include_router(whatsapp.router, prefix="/whatsapp")
app.include_router(users.router)
app.include_router(ironman.router, prefix="/api/ironman")
