from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.crawl_service import CrawlService


settings = get_settings()
scheduler = BackgroundScheduler(timezone="UTC")


def run_daily_crawl() -> None:
    db = SessionLocal()
    try:
        CrawlService(db).crawl_active_items(trigger_source="SCHEDULED")
    finally:
        db.close()


def start_scheduler() -> None:
    if not settings.enable_scheduler:
        return

    if scheduler.running:
        return

    scheduler.add_job(
        run_daily_crawl,
        trigger=CronTrigger(
            hour=settings.scheduler_daily_hour_utc,
            minute=settings.scheduler_daily_minute_utc,
            timezone="UTC",
        ),
        id="daily-ebay-crawl",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
