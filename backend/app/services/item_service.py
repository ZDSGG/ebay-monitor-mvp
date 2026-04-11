from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.crawl_job import CrawlJob
from app.models.enums import EventType, ItemStatus, JobStatus
from app.models.item_event import ItemEvent
from app.models.item_snapshot import ItemSnapshot
from app.models.monitored_item import MonitoredItem
from app.schemas.item import (
    BulkDeleteResponse,
    BulkDeactivateResponse,
    BulkRefreshResponse,
    BulkRefreshResult,
    CrawlSummary,
    DashboardSummaryResponse,
    DashboardTrendPoint,
    ItemDetailResponse,
    ItemEventEntry,
    ItemListEntry,
    ItemSnapshotEntry,
    PriceChangeSummary,
    RecentEventFeedEntry,
    RecentEventListResponse,
)
from app.services.crawl_service import CrawlService
from app.services.url_parser import parse_ebay_item_url


class DuplicateItemError(Exception):
    pass


@dataclass(slots=True)
class _ChangeResult:
    diff: Decimal | None
    rate: Decimal | None
    status: str


class ItemService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crawl_service = CrawlService(db)

    def create_item(self, url: str, note: str | None) -> tuple[MonitoredItem, CrawlSummary]:
        parsed_url = parse_ebay_item_url(url)
        existing_item = self.db.scalar(
            select(MonitoredItem).where(
                MonitoredItem.marketplace == parsed_url.marketplace,
                MonitoredItem.legacy_item_id == parsed_url.legacy_item_id,
            )
        )
        if existing_item:
            raise DuplicateItemError

        item = MonitoredItem(
            marketplace=parsed_url.marketplace,
            legacy_item_id=parsed_url.legacy_item_id,
            url=parsed_url.normalized_url,
            note=note,
            status=ItemStatus.ACTIVE,
        )
        self.db.add(item)
        self.db.flush()

        crawl_job = self.crawl_service.crawl_item(item=item, trigger_source="CREATE_ITEM")
        self.db.commit()
        self.db.refresh(item)
        return item, CrawlSummary(
            status=crawl_job.status.value,
            message="Initial crawl completed." if crawl_job.status.value == "SUCCESS" else "Initial crawl failed.",
        )

    def list_items(self) -> list[ItemListEntry]:
        items = self.db.scalars(select(MonitoredItem).order_by(MonitoredItem.created_at.desc())).all()
        return [self._build_list_entry(item) for item in items]

    def get_item_detail(self, item_id: str) -> ItemDetailResponse | None:
        item = self.db.get(MonitoredItem, item_id)
        if item is None:
            return None

        snapshots = self.db.scalars(
            select(ItemSnapshot)
            .where(
                ItemSnapshot.item_id == item.id,
                ItemSnapshot.capture_time >= utc_now() - timedelta(days=30),
            )
            .order_by(ItemSnapshot.capture_time.asc())
        ).all()
        events = self.db.scalars(
            select(ItemEvent)
            .where(ItemEvent.item_id == item.id)
            .order_by(ItemEvent.event_time.desc())
            .limit(50)
        ).all()

        return ItemDetailResponse(
            id=item.id,
            marketplace=item.marketplace.value,
            legacy_item_id=item.legacy_item_id,
            title=item.title,
            url=item.url,
            note=item.note,
            status=item.status.value,
            currency=item.currency,
            current_price=item.current_price,
            current_shipping_cost=item.current_shipping_cost,
            seller_name=item.seller_name,
            item_condition=item.item_condition,
            availability=item.availability,
            image_url=item.image_url,
            canonical_item_url=item.canonical_item_url,
            last_captured_at=item.last_captured_at,
            thirty_day_snapshots=[
                ItemSnapshotEntry(
                    id=snapshot.id,
                    price=snapshot.price,
                    shipping_cost=snapshot.shipping_cost,
                    total_cost=snapshot.total_cost,
                    capture_time=snapshot.capture_time,
                )
                for snapshot in snapshots
            ],
            recent_events=[
                ItemEventEntry(
                    id=event.id,
                    event_type=event.event_type.value,
                    compare_window=event.compare_window,
                    previous_price=event.previous_price,
                    current_price=event.current_price,
                    diff_amount=event.diff_amount,
                    diff_rate=event.diff_rate,
                    event_time=event.event_time,
                )
                for event in events
            ],
        )

    def get_dashboard_summary(self) -> DashboardSummaryResponse:
        items = self.db.scalars(select(MonitoredItem).order_by(MonitoredItem.created_at.desc())).all()
        list_entries = [self._build_list_entry(item) for item in items]

        now = utc_now()
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_events = self.db.scalars(
            select(ItemEvent).where(
                ItemEvent.event_time >= start_today,
                ItemEvent.compare_window == "1d",
            )
        ).all()
        today_jobs = self.db.scalars(select(CrawlJob).where(CrawlJob.started_at >= start_today)).all()

        today_price_drops = sum(1 for event in today_events if event.event_type == EventType.PRICE_DROP)
        today_price_rises = sum(1 for event in today_events if event.event_type == EventType.PRICE_RISE)
        today_delisted = sum(
            1
            for item in items
            if item.last_captured_at is not None and item.last_captured_at >= start_today and self._is_delisted(item)
        )

        success_count = sum(1 for job in today_jobs if job.status == JobStatus.SUCCESS)
        crawl_success_rate = Decimal("0.00")
        if today_jobs:
            crawl_success_rate = ((Decimal(success_count) / Decimal(len(today_jobs))) * Decimal("100")).quantize(
                Decimal("0.01")
            )

        valid_rates = [abs(entry.yesterday_change.rate) for entry in list_entries if entry.yesterday_change.rate is not None]
        average_volatility = Decimal("0.0000")
        if valid_rates:
            average_volatility = (sum(valid_rates, Decimal("0")) / Decimal(len(valid_rates))).quantize(
                Decimal("0.0001")
            )

        return DashboardSummaryResponse(
            total_items=len(items),
            today_price_drops=today_price_drops,
            today_price_rises=today_price_rises,
            today_delisted=today_delisted,
            crawl_success_rate=crawl_success_rate,
            average_volatility=average_volatility,
            trend_points=self._build_dashboard_trend_points(start_date=start_today.date() - timedelta(days=6)),
        )

    def get_recent_events(self, limit: int = 8) -> RecentEventListResponse:
        rows = self.db.execute(
            select(ItemEvent, MonitoredItem)
            .join(MonitoredItem, MonitoredItem.id == ItemEvent.item_id)
            .where(ItemEvent.event_type != EventType.NO_CHANGE)
            .order_by(ItemEvent.event_time.desc())
            .limit(limit)
        ).all()

        return RecentEventListResponse(
            events=[
                RecentEventFeedEntry(
                    id=event.id,
                    item_id=item.id,
                    item_title=item.title,
                    legacy_item_id=item.legacy_item_id,
                    marketplace=item.marketplace.value,
                    image_url=item.image_url,
                    event_type=event.event_type.value,
                    compare_window=event.compare_window,
                    diff_amount=event.diff_amount,
                    diff_rate=event.diff_rate,
                    event_time=event.event_time,
                )
                for event, item in rows
            ]
        )

    def refresh_items(self, item_ids: list[UUID]) -> BulkRefreshResponse:
        unique_ids = list(dict.fromkeys(item_ids))
        items = self.db.scalars(select(MonitoredItem).where(MonitoredItem.id.in_(unique_ids))).all()

        results: list[BulkRefreshResult] = []
        success_count = 0
        failed_count = 0

        for item in items:
            crawl_job = self.crawl_service.crawl_item(item=item, trigger_source="MANUAL")
            if crawl_job.status == JobStatus.SUCCESS:
                success_count += 1
                message = "Refresh completed."
            else:
                failed_count += 1
                message = crawl_job.error_message or "Refresh failed."

            results.append(
                BulkRefreshResult(
                    item_id=item.id,
                    title=item.title,
                    status=crawl_job.status.value,
                    message=message,
                )
            )

        self.db.commit()
        return BulkRefreshResponse(
            requested_count=len(unique_ids),
            processed_count=len(items),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
        )

    def deactivate_items(self, item_ids: list[UUID]) -> BulkDeactivateResponse:
        unique_ids = list(dict.fromkeys(item_ids))
        items = self.db.scalars(select(MonitoredItem).where(MonitoredItem.id.in_(unique_ids))).all()
        for item in items:
            item.status = ItemStatus.INACTIVE

        self.db.commit()
        return BulkDeactivateResponse(
            requested_count=len(unique_ids),
            deactivated_count=len(items),
        )

    def delete_items(self, item_ids: list[UUID]) -> BulkDeleteResponse:
        unique_ids = list(dict.fromkeys(item_ids))
        items = self.db.scalars(select(MonitoredItem).where(MonitoredItem.id.in_(unique_ids))).all()
        deleted_count = len(items)

        for item in items:
            self.db.delete(item)

        self.db.commit()
        return BulkDeleteResponse(
            requested_count=len(unique_ids),
            deleted_count=deleted_count,
        )

    def delete_item(self, item_id: str) -> bool:
        item = self.db.get(MonitoredItem, item_id)
        if item is None:
            return False

        self.db.delete(item)
        self.db.commit()
        return True

    def update_item_note(self, item_id: str, note: str | None) -> MonitoredItem | None:
        item = self.db.get(MonitoredItem, item_id)
        if item is None:
            return None

        item.note = note
        self.db.commit()
        self.db.refresh(item)
        return item

    def _build_list_entry(self, item: MonitoredItem) -> ItemListEntry:
        latest_snapshot = self.db.scalar(
            select(ItemSnapshot)
            .where(ItemSnapshot.item_id == item.id)
            .order_by(ItemSnapshot.capture_time.desc())
            .limit(1)
        )

        now = utc_now()
        yesterday_snapshot = self.db.scalar(
            select(ItemSnapshot)
            .where(
                ItemSnapshot.item_id == item.id,
                ItemSnapshot.capture_time <= now - timedelta(days=1),
            )
            .order_by(ItemSnapshot.capture_time.desc())
            .limit(1)
        )
        weekly_snapshot = self.db.scalar(
            select(ItemSnapshot)
            .where(
                ItemSnapshot.item_id == item.id,
                ItemSnapshot.capture_time <= now - timedelta(days=7),
            )
            .order_by(ItemSnapshot.capture_time.desc())
            .limit(1)
        )
        recent_snapshots = self.db.scalars(
            select(ItemSnapshot)
            .where(
                ItemSnapshot.item_id == item.id,
                ItemSnapshot.capture_time >= now - timedelta(days=7),
            )
            .order_by(ItemSnapshot.capture_time.asc())
            .limit(7)
        ).all()
        latest_event = self.db.scalar(
            select(ItemEvent)
            .where(
                ItemEvent.item_id == item.id,
                ItemEvent.event_type != EventType.NO_CHANGE,
            )
            .order_by(ItemEvent.event_time.desc())
            .limit(1)
        )

        current_total_cost = latest_snapshot.total_cost if latest_snapshot else self._calculate_total_cost(
            item.current_price,
            item.current_shipping_cost,
        )
        yesterday_change = self._calculate_change(
            current_price=latest_snapshot.price if latest_snapshot else item.current_price,
            previous_price=yesterday_snapshot.price if yesterday_snapshot else None,
        )
        weekly_change = self._calculate_change(
            current_price=latest_snapshot.price if latest_snapshot else item.current_price,
            previous_price=weekly_snapshot.price if weekly_snapshot else None,
        )

        return ItemListEntry(
            id=item.id,
            marketplace=item.marketplace.value,
            legacy_item_id=item.legacy_item_id,
            title=item.title,
            url=item.url,
            note=item.note,
            seller_name=item.seller_name,
            availability=item.availability,
            image_url=item.image_url,
            currency=item.currency,
            current_price=latest_snapshot.price if latest_snapshot else item.current_price,
            current_shipping_cost=latest_snapshot.shipping_cost if latest_snapshot else item.current_shipping_cost,
            total_cost=current_total_cost,
            yesterday_change=PriceChangeSummary(
                diff=yesterday_change.diff,
                rate=yesterday_change.rate,
                status=yesterday_change.status,
            ),
            weekly_change=PriceChangeSummary(
                diff=weekly_change.diff,
                rate=weekly_change.rate,
                status=weekly_change.status,
            ),
            is_price_drop=yesterday_change.status == "PRICE_DROP" or weekly_change.status == "PRICE_DROP",
            last_captured_at=item.last_captured_at,
            status=item.status.value,
            latest_event_type=latest_event.event_type.value if latest_event else None,
            latest_event_time=latest_event.event_time if latest_event else None,
            recent_prices=[snapshot.price for snapshot in recent_snapshots],
        )

    def _build_dashboard_trend_points(self, start_date: date) -> list[DashboardTrendPoint]:
        start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        snapshots = self.db.scalars(
            select(ItemSnapshot)
            .where(ItemSnapshot.capture_time >= start_datetime)
            .order_by(ItemSnapshot.capture_time.asc())
        ).all()

        buckets: dict[date, list[Decimal]] = {}
        for snapshot in snapshots:
            bucket = snapshot.capture_time.date()
            buckets.setdefault(bucket, []).append(snapshot.price)

        points: list[DashboardTrendPoint] = []
        for offset in range(7):
            current_date = start_date + timedelta(days=offset)
            prices = buckets.get(current_date, [])
            average_price = Decimal("0.00")
            if prices:
                average_price = (sum(prices, Decimal("0")) / Decimal(len(prices))).quantize(Decimal("0.01"))

            points.append(
                DashboardTrendPoint(
                    capture_date=current_date,
                    average_price=average_price,
                    item_count=len(prices),
                )
            )

        return points

    def _calculate_change(
        self,
        current_price: Decimal | None,
        previous_price: Decimal | None,
    ) -> _ChangeResult:
        if current_price is None or previous_price is None:
            return _ChangeResult(diff=None, rate=None, status="NO_DATA")

        diff = current_price - previous_price
        if abs(diff) < Decimal("0.01"):
            return _ChangeResult(diff=Decimal("0.00"), rate=Decimal("0.0000"), status="NO_CHANGE")

        rate = None if previous_price == Decimal("0") else (diff / previous_price).quantize(Decimal("0.0001"))
        status = "PRICE_DROP" if diff < 0 else "PRICE_RISE"
        return _ChangeResult(diff=diff.quantize(Decimal("0.01")), rate=rate, status=status)

    def _calculate_total_cost(
        self,
        price: Decimal | None,
        shipping_cost: Decimal | None,
    ) -> Decimal | None:
        if price is None:
            return None
        shipping = shipping_cost or Decimal("0.00")
        return (price + shipping).quantize(Decimal("0.01"))

    def _is_delisted(self, item: MonitoredItem) -> bool:
        if item.status == ItemStatus.INACTIVE:
            return True

        availability = (item.availability or "").lower()
        return any(token in availability for token in ("unavailable", "out of stock", "sold"))
