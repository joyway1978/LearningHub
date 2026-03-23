"""
Scheduler Module for AI Learning Platform

Provides scheduled task management using APScheduler.
Handles cleanup tasks and other periodic maintenance operations.
"""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.cleanup import run_cleanup

# Configure logger
logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None

# Default schedule for cleanup task (daily at 3:00 AM)
DEFAULT_CLEANUP_HOUR = 3
DEFAULT_CLEANUP_MINUTE = 0


class SchedulerConfig:
    """Configuration for the scheduler."""

    def __init__(
        self,
        cleanup_enabled: bool = True,
        cleanup_hour: int = DEFAULT_CLEANUP_HOUR,
        cleanup_minute: int = DEFAULT_CLEANUP_MINUTE,
        timezone: str = "UTC"
    ):
        self.cleanup_enabled = cleanup_enabled
        self.cleanup_hour = cleanup_hour
        self.cleanup_minute = cleanup_minute
        self.timezone = timezone


def _on_job_executed(event):
    """Callback for successful job execution."""
    if event.exception:
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} completed successfully")


def _on_job_error(event):
    """Callback for job execution error."""
    logger.error(f"Job {event.job_id} raised an exception: {event.exception}")


async def _cleanup_job():
    """
    The actual cleanup job that runs on schedule.

    This is an async wrapper around the sync cleanup function.
    """
    logger.info("Running scheduled cleanup task")
    try:
        result = run_cleanup()
        logger.info(
            f"Scheduled cleanup completed: "
            f"{result.cleaned_records} records, "
            f"{result.cleaned_files} files cleaned, "
            f"duration: {result.duration_seconds:.2f}s"
        )
        if result.errors:
            logger.warning(f"Cleanup completed with {len(result.errors)} errors")
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}")


def create_scheduler(config: Optional[SchedulerConfig] = None) -> AsyncIOScheduler:
    """
    Create and configure the scheduler.

    Args:
        config: Scheduler configuration. Uses defaults if not provided.

    Returns:
        Configured AsyncIOScheduler instance
    """
    if config is None:
        config = SchedulerConfig()

    scheduler = AsyncIOScheduler(timezone=config.timezone)

    # Add event listeners for logging
    scheduler.add_listener(_on_job_executed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Add cleanup job if enabled
    if config.cleanup_enabled:
        scheduler.add_job(
            _cleanup_job,
            trigger=CronTrigger(
                hour=config.cleanup_hour,
                minute=config.cleanup_minute
            ),
            id="daily_cleanup",
            name="Daily Cleanup Task",
            replace_existing=True,
            misfire_grace_time=3600  # Allow 1 hour grace time for missed jobs
        )
        logger.info(
            f"Scheduled daily cleanup at {config.cleanup_hour:02d}:{config.cleanup_minute:02d} "
            f"({config.timezone})"
        )

    return scheduler


def init_scheduler(config: Optional[SchedulerConfig] = None) -> AsyncIOScheduler:
    """
    Initialize the global scheduler instance.

    Args:
        config: Scheduler configuration

    Returns:
        The initialized scheduler
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already initialized, shutting down existing scheduler")
        shutdown_scheduler()

    _scheduler = create_scheduler(config)
    logger.info("Scheduler initialized")

    return _scheduler


def start_scheduler() -> None:
    """Start the scheduler."""
    global _scheduler

    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")

    if not _scheduler.running:
        _scheduler.start()
        logger.info("Scheduler started")
    else:
        logger.warning("Scheduler is already running")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler."""
    global _scheduler

    if _scheduler is not None:
        if _scheduler.running:
            _scheduler.shutdown(wait=True)
            logger.info("Scheduler shutdown complete")
        _scheduler = None
    else:
        logger.warning("Scheduler not initialized, nothing to shutdown")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """
    Get the current scheduler instance.

    Returns:
        The scheduler instance or None if not initialized
    """
    return _scheduler


def is_scheduler_running() -> bool:
    """
    Check if the scheduler is running.

    Returns:
        True if scheduler is running, False otherwise
    """
    return _scheduler is not None and _scheduler.running


def get_scheduled_jobs() -> list:
    """
    Get a list of scheduled jobs.

    Returns:
        List of job information dictionaries
    """
    if _scheduler is None:
        return []

    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })

    return jobs


async def trigger_cleanup_now() -> dict:
    """
    Manually trigger the cleanup job.

    Returns:
        Cleanup result dictionary
    """
    logger.info("Manually triggering cleanup job")
    result = run_cleanup()
    return result.to_dict()


def pause_job(job_id: str) -> bool:
    """
    Pause a scheduled job.

    Args:
        job_id: ID of the job to pause

    Returns:
        True if job was paused, False otherwise
    """
    if _scheduler is None:
        return False

    job = _scheduler.get_job(job_id)
    if job:
        job.pause()
        logger.info(f"Job {job_id} paused")
        return True
    return False


def resume_job(job_id: str) -> bool:
    """
    Resume a paused job.

    Args:
        job_id: ID of the job to resume

    Returns:
        True if job was resumed, False otherwise
    """
    if _scheduler is None:
        return False

    job = _scheduler.get_job(job_id)
    if job:
        job.resume()
        logger.info(f"Job {job_id} resumed")
        return True
    return False
