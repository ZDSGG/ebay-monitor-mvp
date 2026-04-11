from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.enums import JobStatus
from app.schemas.ops import CrawlTriggerResponse
from app.services.crawl_service import CrawlService


router = APIRouter(prefix="/ops", tags=["ops"])
settings = get_settings()


@router.post("/run-daily-crawl", response_model=CrawlTriggerResponse)
def run_daily_crawl(
    x_cron_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CrawlTriggerResponse:
    if not settings.cron_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRON_SECRET is not configured.",
        )

    if x_cron_secret != settings.cron_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret.",
        )

    jobs = CrawlService(db).crawl_active_items(trigger_source="CRON")
    return CrawlTriggerResponse(
        requested=len(jobs),
        succeeded=sum(1 for job in jobs if job.status == JobStatus.SUCCESS),
        failed=sum(1 for job in jobs if job.status == JobStatus.FAILED),
        trigger_source="CRON",
    )
