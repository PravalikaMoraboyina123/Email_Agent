"""
APScheduler Background Scheduler Configuration for InboxPilot AI.
Automates 6:00 AM Morning Routine, 9:00 PM Evening Routine, and 24/7 Continuous Email Monitoring.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from agents.email_agent import agent
from config.settings import settings
from utils.logger import logger

scheduler = BackgroundScheduler(daemon=True)


def trigger_live_scan_job():
    """Wrapper function executing live scan daemon job."""
    logger.info("[CRON JOB] Executing continuous live email scan...")
    try:
        agent.process_new_emails()
    except Exception as e:
        logger.error(f"[CRON JOB ERROR] Live scan failed: {e}")


def trigger_morning_routine_job():
    """Wrapper function executing 6:00 AM Morning Routine."""
    logger.info("[CRON JOB] Executing Morning Briefing Routine (6:00 AM)...")
    try:
        agent.run_morning_routine()
    except Exception as e:
        logger.error(f"[CRON JOB ERROR] Morning routine failed: {e}")


def trigger_evening_routine_job():
    """Wrapper function executing 9:00 PM Evening Routine."""
    logger.info("[CRON JOB] Executing Evening Briefing Routine (9:00 PM)...")
    try:
        agent.run_evening_routine()
    except Exception as e:
        logger.error(f"[CRON JOB ERROR] Evening routine failed: {e}")


def start_scheduler():
    """
    Initializes and starts the APScheduler background daemon tasks.
    """
    if scheduler.running:
        logger.warning("Scheduler daemon is already active.")
        return

    # 1. Register Live Email Scan (Every X seconds)
    scheduler.add_job(
        trigger_live_scan_job,
        trigger=IntervalTrigger(seconds=settings.EMAIL_CHECK_INTERVAL_SECONDS),
        id="live_email_scan_job",
        name="Live Continuous Email Scanner",
        replace_existing=True
    )

    # 2. Register Morning Routine (6:00 AM)
    morning_hour, morning_minute = map(int, settings.MORNING_ROUTINE_TIME.split(":"))
    scheduler.add_job(
        trigger_morning_routine_job,
        trigger=CronTrigger(hour=morning_hour, minute=morning_minute),
        id="morning_routine_job",
        name="6:00 AM Morning Briefing Routine",
        replace_existing=True
    )

    # 3. Register Evening Routine (9:00 PM)
    evening_hour, evening_minute = map(int, settings.EVENING_ROUTINE_TIME.split(":"))
    scheduler.add_job(
        trigger_evening_routine_job,
        trigger=CronTrigger(hour=evening_hour, minute=evening_minute),
        id="evening_routine_job",
        name="9:00 PM Evening Briefing Routine",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"APScheduler daemon initialized successfully! Schedules: Live Scan ({settings.LIVE_SCAN_INTERVAL_MINUTES}m), Morning ({settings.MORNING_ROUTINE_TIME}), Evening ({settings.EVENING_ROUTINE_TIME}).")


def stop_scheduler():
    """
    Shuts down APScheduler gracefully during FastAPI application teardown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler daemon shut down gracefully.")
