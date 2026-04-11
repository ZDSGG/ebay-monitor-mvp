from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.crawl_job import CrawlJob
from app.models.enums import ItemStatus, JobStatus
from app.models.monitored_item import MonitoredItem
from app.services.ebay_client import EbayClient
from app.services.event_service import EventService
from app.services.snapshot_service import SnapshotService


class CrawlService:
    def __init__(self, db: Session, ebay_client: EbayClient | None = None) -> None:
        self.db = db
        self.ebay_client = ebay_client or EbayClient()
        self.snapshot_service = SnapshotService(db)
        self.event_service = EventService(db)

    def crawl_item(self, item: MonitoredItem, trigger_source: str) -> CrawlJob:
        crawl_job = CrawlJob(
            item_id=item.id,
            status=JobStatus.PENDING,
            trigger_source=trigger_source,
        )
        self.db.add(crawl_job)
        self.db.flush()

        try:
            ebay_data = self.ebay_client.get_item_by_legacy_id(
                legacy_item_id=item.legacy_item_id,
                marketplace_id=item.marketplace.value,
            )
            capture_time = utc_now()
            item.title = ebay_data.title
            item.currency = ebay_data.currency
            item.current_price = ebay_data.price
            item.current_shipping_cost = ebay_data.shipping_cost
            item.seller_name = ebay_data.seller_name
            item.item_condition = ebay_data.condition
            item.availability = ebay_data.availability
            item.image_url = ebay_data.image
            item.canonical_item_url = ebay_data.item_url
            item.last_captured_at = capture_time

            snapshot = self.snapshot_service.create_snapshot(
                item=item,
                price=ebay_data.price,
                shipping_cost=ebay_data.shipping_cost,
                capture_time=capture_time,
            )
            self.event_service.analyze_and_record_events(item=item, current_snapshot=snapshot)

            crawl_job.status = JobStatus.SUCCESS
            crawl_job.finished_at = utc_now()
        except Exception as exc:
            crawl_job.status = JobStatus.FAILED
            crawl_job.finished_at = utc_now()
            crawl_job.error_message = str(exc)

        self.db.flush()
        return crawl_job

    def crawl_active_items(self, trigger_source: str = "SCHEDULED") -> list[CrawlJob]:
        items = self.db.scalars(
            select(MonitoredItem).where(MonitoredItem.status == ItemStatus.ACTIVE)
        ).all()
        jobs: list[CrawlJob] = []
        for item in items:
            jobs.append(self.crawl_item(item=item, trigger_source=trigger_source))
        self.db.commit()
        return jobs
