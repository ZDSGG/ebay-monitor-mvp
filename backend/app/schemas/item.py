from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class MonitoredItemCreateRequest(BaseModel):
    url: HttpUrl
    note: str | None = None


class UpdateItemNoteRequest(BaseModel):
    note: str | None = None


class BulkItemActionRequest(BaseModel):
    item_ids: list[UUID]


class CrawlSummary(BaseModel):
    status: str
    message: str


class MonitoredItemResponse(BaseModel):
    id: UUID
    marketplace: str
    legacy_item_id: str
    url: str
    note: str | None
    status: str
    title: str | None
    currency: str | None
    current_price: Decimal | None
    current_shipping_cost: Decimal | None
    seller_name: str | None
    item_condition: str | None
    availability: str | None
    image_url: str | None
    canonical_item_url: str | None
    last_captured_at: datetime | None
    created_at: datetime
    updated_at: datetime
    initial_crawl: CrawlSummary

    model_config = ConfigDict(from_attributes=True)


class PriceChangeSummary(BaseModel):
    diff: Decimal | None
    rate: Decimal | None
    status: str


class ItemListEntry(BaseModel):
    id: UUID
    marketplace: str
    legacy_item_id: str
    title: str | None
    url: str
    note: str | None
    seller_name: str | None
    availability: str | None
    image_url: str | None
    currency: str | None
    current_price: Decimal | None
    current_shipping_cost: Decimal | None
    total_cost: Decimal | None
    yesterday_change: PriceChangeSummary
    weekly_change: PriceChangeSummary
    is_price_drop: bool
    last_captured_at: datetime | None
    status: str
    latest_event_type: str | None
    latest_event_time: datetime | None
    recent_prices: list[Decimal]


class ItemListResponse(BaseModel):
    items: list[ItemListEntry]


class ItemEventEntry(BaseModel):
    id: UUID
    event_type: str
    compare_window: str
    previous_price: Decimal | None
    current_price: Decimal
    diff_amount: Decimal | None
    diff_rate: Decimal | None
    event_time: datetime


class ItemSnapshotEntry(BaseModel):
    id: UUID
    price: Decimal
    shipping_cost: Decimal
    total_cost: Decimal
    capture_time: datetime


class ItemDetailResponse(BaseModel):
    id: UUID
    marketplace: str
    legacy_item_id: str
    title: str | None
    url: str
    note: str | None
    status: str
    currency: str | None
    current_price: Decimal | None
    current_shipping_cost: Decimal | None
    seller_name: str | None
    item_condition: str | None
    availability: str | None
    image_url: str | None
    canonical_item_url: str | None
    last_captured_at: datetime | None
    thirty_day_snapshots: list[ItemSnapshotEntry]
    recent_events: list[ItemEventEntry]


class DashboardTrendPoint(BaseModel):
    capture_date: date
    average_price: Decimal
    item_count: int


class DashboardSummaryResponse(BaseModel):
    total_items: int
    today_price_drops: int
    today_price_rises: int
    today_delisted: int
    crawl_success_rate: Decimal
    average_volatility: Decimal
    trend_points: list[DashboardTrendPoint]


class RecentEventFeedEntry(BaseModel):
    id: UUID
    item_id: UUID
    item_title: str | None
    legacy_item_id: str
    marketplace: str
    image_url: str | None
    event_type: str
    compare_window: str
    diff_amount: Decimal | None
    diff_rate: Decimal | None
    event_time: datetime


class RecentEventListResponse(BaseModel):
    events: list[RecentEventFeedEntry]


class BulkRefreshResult(BaseModel):
    item_id: UUID
    title: str | None
    status: str
    message: str


class BulkRefreshResponse(BaseModel):
    requested_count: int
    processed_count: int
    success_count: int
    failed_count: int
    results: list[BulkRefreshResult]


class BulkDeactivateResponse(BaseModel):
    requested_count: int
    deactivated_count: int


class BulkDeleteResponse(BaseModel):
    requested_count: int
    deleted_count: int
