from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from irony import cache
from irony.config import config
from irony.config.logger import logger
from irony.routers import users, whatsapp, ironman
from irony.util import background_process

# Initialize the scheduler
scheduler = AsyncIOScheduler()

# Add the job to the scheduler
# TODO add this back when you want to send ironman_request
scheduler.add_job(
    background_process.send_pending_order_requests, CronTrigger(minute="*/1")
)

scheduler.add_job(
    background_process.send_ironman_delivery_schedule, CronTrigger(minute="*/1")
)

scheduler.add_job(
    background_process.send_ironman_work_schedule, CronTrigger(minute="*/2")
)

scheduler.add_job(
    background_process.send_ironman_pending_work_schedule, CronTrigger(minute="*/1")
)


# Runs every 1 minute

# scheduler.add_job(
#     background_process.send_ironman_request, CronTrigger(minute="*/1")
# )  # Runs every 1 minute


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event equivalent
    config.DB_CACHE = await cache.fetch_data_from_db(config.DB_CACHE)
    logger.info("Data loaded into cache")
    scheduler.start()
    # await background_process.send_pending_order_requests()
    logger.info("Scheduler started")
    # Yield control to the app
    try:
        yield
    finally:
        # Shutdown the scheduler
        scheduler.shutdown()
    # Shutdown event equivalent
    logger.info("Application shutdown, you can clean up resources here")


app = FastAPI()

app.router.lifespan_context = lifespan


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(whatsapp.router, prefix="/whatsapp")
app.include_router(users.router)
app.include_router(ironman.router, prefix="/ironman")
