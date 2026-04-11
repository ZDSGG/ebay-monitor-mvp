from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.crawl_job import CrawlJob
from app.models.enums import JobStatus, ListingStatus, ShopStatus
from app.models.shop import Shop
from app.models.shop_daily_stat import ShopDailyStat
from app.models.shop_listing import ShopListing
from app.services.alert_service import AlertService
from app.services.ebay_client import EbayClient


@dataclass(slots=True)
class ShopListingSnapshot:
    legacy_item_id: str
    title: str
    item_url: str
    image_url: str | None
    currency: str | None
    price: Decimal | None
    shipping_cost: Decimal | None
    total_cost: Decimal | None
    availability: str | None


class ShopScanService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.ebay_client = EbayClient()
        self.alert_service = AlertService(db)

    def scan_active_shops(self, trigger_source: str) -> list[CrawlJob]:
        shops = self.db.scalars(
            select(Shop).where(
                Shop.status == ShopStatus.ACTIVE,
                Shop.scan_enabled.is_(True),
            )
        ).all()

        jobs: list[CrawlJob] = []
        for shop in shops:
            jobs.append(self.scan_shop(shop=shop, trigger_source=trigger_source))

        self.db.commit()
        return jobs

    def scan_shop(self, shop: Shop, trigger_source: str) -> CrawlJob:
        job = CrawlJob(
            shop_id=shop.id,
            status=JobStatus.PENDING,
            trigger_source=trigger_source,
        )
        self.db.add(job)
        self.db.flush()

        try:
            snapshots = self.ebay_client.search_items_by_seller_username(
                seller_username=shop.seller_username,
                marketplace_id=shop.marketplace.value,
            )
            stat = self._sync_shop_listings(shop=shop, snapshots=snapshots)
            self.alert_service.ensure_default_rules(shop)
            self.alert_service.evaluate_shop_rules(shop=shop, current_stat=stat)
            shop.last_scanned_at = utc_now()
            job.status = JobStatus.SUCCESS
            job.finished_at = utc_now()
            return job
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.finished_at = utc_now()
            return job

    def _sync_shop_listings(self, shop: Shop, snapshots: list[ShopListingSnapshot]) -> ShopDailyStat:
        now = utc_now()
        existing_listings = self.db.scalars(select(ShopListing).where(ShopListing.shop_id == shop.id)).all()
        listing_map = {listing.legacy_item_id: listing for listing in existing_listings}

        active_ids: set[str] = set()
        new_listing_count = 0
        ended_listing_count = 0
        price_drop_count = 0
        price_rise_count = 0
        total_prices: list[Decimal] = []

        for snapshot in snapshots:
            active_ids.add(snapshot.legacy_item_id)
            if snapshot.price is not None:
                total_prices.append(snapshot.price)

            existing = listing_map.get(snapshot.legacy_item_id)
            if existing is None:
                new_listing_count += 1
                self.db.add(
                    ShopListing(
                        shop_id=shop.id,
                        legacy_item_id=snapshot.legacy_item_id,
                        title=snapshot.title,
                        item_url=snapshot.item_url,
                        image_url=snapshot.image_url,
                        currency=snapshot.currency,
                        current_price=snapshot.price,
                        current_shipping_cost=snapshot.shipping_cost,
                        total_cost=snapshot.total_cost,
                        availability=snapshot.availability,
                        listing_status=ListingStatus.ACTIVE,
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )
                continue

            previous_price = existing.current_price
            existing.title = snapshot.title
            existing.item_url = snapshot.item_url
            existing.image_url = snapshot.image_url
            existing.currency = snapshot.currency
            existing.current_price = snapshot.price
            existing.current_shipping_cost = snapshot.shipping_cost
            existing.total_cost = snapshot.total_cost
            existing.availability = snapshot.availability
            existing.listing_status = ListingStatus.ACTIVE
            existing.last_seen_at = now

            if previous_price is not None and snapshot.price is not None:
                if snapshot.price < previous_price:
                    price_drop_count += 1
                    existing.last_price_change_at = now
                elif snapshot.price > previous_price:
                    price_rise_count += 1
                    existing.last_price_change_at = now

        for listing in existing_listings:
            if listing.legacy_item_id in active_ids:
                continue
            if listing.listing_status != ListingStatus.ENDED:
                ended_listing_count += 1
            listing.listing_status = ListingStatus.ENDED

        average_price = None
        if total_prices:
            average_price = (sum(total_prices, Decimal("0")) / Decimal(len(total_prices))).quantize(Decimal("0.01"))

        stat_date = now.date()
        stat = self.db.scalar(
            select(ShopDailyStat).where(
                ShopDailyStat.shop_id == shop.id,
                ShopDailyStat.stat_date == stat_date,
            )
        )
        active_listing_count = len(active_ids)

        if stat is None:
            stat = ShopDailyStat(
                shop_id=shop.id,
                stat_date=stat_date,
            )
            self.db.add(stat)

        stat.active_listing_count = active_listing_count
        stat.new_listing_count = new_listing_count
        stat.ended_listing_count = ended_listing_count
        stat.price_drop_count = price_drop_count
        stat.price_rise_count = price_rise_count
        stat.average_price = average_price
        stat.scanned_at = now
        return stat
