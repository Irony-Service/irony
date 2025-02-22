import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from irony.config.logger import logger
from irony.file_lock import FileLockError, file_lock
from irony.util import background_process

# Define lock files for each process
LOCK_FILES = {
    "reset_daily_config": os.path.join(
        os.path.dirname(__file__), "locks", "reset_daily_config.lock"
    ),
    "pending_orders": os.path.join(
        os.path.dirname(__file__), "locks", "pending_orders.lock"
    ),
    "delivery_schedule": os.path.join(
        os.path.dirname(__file__), "locks", "delivery_schedule.lock"
    ),
    "work_schedule": os.path.join(
        os.path.dirname(__file__), "locks", "work_schedule.lock"
    ),
    "pending_work": os.path.join(
        os.path.dirname(__file__), "locks", "pending_work.lock"
    ),
    "timeslot_volume": os.path.join(
        os.path.dirname(__file__), "locks", "timeslot_volume.lock"
    ),
    "order_requests": os.path.join(
        os.path.dirname(__file__), "locks", "order_requests.lock"
    ),
    "reassign_orders": os.path.join(
        os.path.dirname(__file__), "locks", "reassign_orders.lock"
    ),
}


# Create individual background task functions for each process
async def execute_reset_daily_config():
    try:
        with file_lock(LOCK_FILES["reset_daily_config"]):
            await background_process.reset_daily_config()
            logger.info("Completed reset_daily_config")
    except FileLockError:
        logger.warning("Skipping reset_daily_config - already running")
    except Exception as e:
        logger.error(f"Error in reset_daily_config: {e}")


async def execute_pending_orders():
    try:
        with file_lock(LOCK_FILES["pending_orders"]):
            await background_process.send_pending_order_requests()
            logger.info("Completed send_pending_order_requests")
    except FileLockError:
        logger.warning("Skipping send_pending_order_requests - already running")
    except Exception as e:
        logger.error(f"Error in send_pending_order_requests: {e}")


async def execute_delivery_schedule():
    try:
        with file_lock(LOCK_FILES["delivery_schedule"]):
            await background_process.send_ironman_delivery_schedule()
            logger.info("Completed send_ironman_delivery_schedule")
    except FileLockError:
        logger.warning("Skipping send_ironman_delivery_schedule - already running")
    except Exception as e:
        logger.error(f"Error in send_ironman_delivery_schedule: {e}")


async def execute_work_schedule():
    try:
        with file_lock(LOCK_FILES["work_schedule"]):
            await background_process.send_ironman_work_schedule()
            logger.info("Completed send_ironman_work_schedule")
    except FileLockError:
        logger.warning("Skipping send_ironman_work_schedule - already running")
    except Exception as e:
        logger.error(f"Error in send_ironman_work_schedule: {e}")


async def execute_pending_work():
    try:
        with file_lock(LOCK_FILES["pending_work"]):
            await background_process.send_ironman_pending_work_schedule()
            logger.info("Completed send_ironman_pending_work_schedule")
    except FileLockError:
        logger.warning("Skipping send_ironman_pending_work_schedule - already running")
    except Exception as e:
        logger.error(f"Error in send_ironman_pending_work_schedule: {e}")


async def execute_timeslot_volume():
    try:
        with file_lock(LOCK_FILES["timeslot_volume"]):
            await background_process.create_timeslot_volume_record()
            logger.info("Completed create_timeslot_volume_record")
    except FileLockError:
        logger.warning("Skipping create_timeslot_volume_record - already running")
    except Exception as e:
        logger.error(f"Error in create_timeslot_volume_record: {e}")


async def execute_order_requests():
    try:
        with file_lock(LOCK_FILES["order_requests"]):
            await background_process.create_order_requests()
            logger.info("Completed create_order_requests")
    except FileLockError:
        logger.warning("Skipping create_order_requests - already running")
    except Exception as e:
        logger.error(f"Error in create_order_requests: {e}")


async def execute_reassign_orders():
    try:
        with file_lock(LOCK_FILES["reassign_orders"]):
            await background_process.reassign_missed_orders()
            logger.info("Completed reassign_missed_orders")
    except FileLockError:
        logger.warning("Skipping reassign_missed_orders - already running")
    except Exception as e:
        logger.error(f"Error in reassign_missed_orders: {e}")


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler with all jobs"""
    scheduler = AsyncIOScheduler()

    # Add all scheduled jobs
    scheduler.add_job(execute_reset_daily_config, CronTrigger(minute="*/5"))
    scheduler.add_job(execute_pending_orders, CronTrigger(minute="*/2"))
    scheduler.add_job(execute_delivery_schedule, CronTrigger(minute="*/3"))
    scheduler.add_job(execute_work_schedule, CronTrigger(minute="*/3"))
    scheduler.add_job(execute_pending_work, CronTrigger(minute="*/2"))
    scheduler.add_job(execute_timeslot_volume, CronTrigger(minute="*/5"))
    scheduler.add_job(execute_order_requests, CronTrigger(minute="*/1"))
    scheduler.add_job(execute_reassign_orders, CronTrigger(minute="*/2"))

    return scheduler
