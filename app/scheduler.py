# FILE: app/scheduler.py

"""
APScheduler integration for URL Monitor
Manages scheduled execution of URL checks.
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import utc

from app.config import get_config
from app.checker import run_all_checks

logger = logging.getLogger(__name__)

def start_scheduler():
    """
    Initializes and starts the scheduler based on settings from config.
    """
    config = get_config()
    
    if not config.get('scheduler.enabled', True):
        logger.info("Scheduler is disabled in configuration.")
        return

    scheduler = BlockingScheduler(timezone=utc)
    schedules = config.get('scheduler.schedules', ["06:00", "14:00", "20:00"])
    
    if not schedules:
        logger.warning("No schedules found in configuration. Scheduler will not run.")
        return

    logger.info("Configuring scheduler...")
    for i, schedule_time in enumerate(schedules):
        try:
            hour, minute = map(int, schedule_time.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute, timezone=utc)
            scheduler.add_job(
                run_all_checks,
                trigger=trigger,
                id=f'url_check_job_{i}',
                name=f'URL Check at {schedule_time} UTC',
                replace_existing=True
            )
            logger.info(f"Scheduled job to run daily at {schedule_time} UTC.")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid schedule format '{schedule_time}'. Skipping. Error: {e}")

    if not scheduler.get_jobs():
        logger.error("No valid jobs were scheduled. Exiting scheduler.")
        return
        
    try:
        logger.info("Scheduler started. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
    finally:
        if scheduler.running:
            scheduler.shutdown()