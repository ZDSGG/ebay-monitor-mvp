from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class ShopCreateRequest(BaseModel):
    url: HttpUrl
    note: str | None = None


class ShopScanSummary(BaseModel):
    status: str
    message: str


class ShopResponse(BaseModel):
    id: UUID
    marketplace: str
    seller_username: str
    shop_name: str
    shop_url: str
    note: str | None
    status: str
    scan_enabled: bool
    last_scanned_at: datetime | None
    created_at: datetime
    updated_at: datetime
    initial_scan: ShopScanSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class ShopListResponse(BaseModel):
    shops: list[ShopResponse]


class ShopDailyStatEntry(BaseModel):
    id: UUID
    stat_date: date
    active_listing_count: int
    new_listing_count: int
    ended_listing_count: int
    price_drop_count: int
    price_rise_count: int
    average_price: Decimal | None
    scanned_at: datetime


class ShopScanTriggerResponse(BaseModel):
    requested: int
    succeeded: int
    failed: int
    trigger_source: str


class ShopListingEntry(BaseModel):
    id: UUID
    legacy_item_id: str
    title: str
    item_url: str
    image_url: str | None
    currency: str | None
    current_price: Decimal | None
    current_shipping_cost: Decimal | None
    total_cost: Decimal | None
    availability: str | None
    sales_summary: str | None
    listing_status: str
    first_seen_at: datetime
    last_seen_at: datetime
    last_price_change_at: datetime | None


class ShopPortrait(BaseModel):
    active_listing_count: int
    active_ratio: Decimal
    average_price: Decimal | None
    last_7d_new_count: int
    last_7d_ended_count: int
    last_7d_price_drop_count: int
    open_alert_count: int


class ShopDetailResponse(BaseModel):
    id: UUID
    marketplace: str
    seller_username: str
    shop_name: str
    shop_url: str
    note: str | None
    status: str
    scan_enabled: bool
    last_scanned_at: datetime | None
    created_at: datetime
    updated_at: datetime
    portrait: ShopPortrait
    recent_stats: list[ShopDailyStatEntry]
    active_listings: list[ShopListingEntry]
