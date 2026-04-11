from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.enums import AlertStatus, ListingStatus
from app.models.enums import ShopStatus
from app.models.shop import Shop
from app.models.shop_daily_stat import ShopDailyStat
from app.models.shop_listing import ShopListing
from app.schemas.shop import (
    ShopDailyStatEntry,
    ShopDetailResponse,
    ShopListingEntry,
    ShopPortrait,
    ShopResponse,
    ShopScanSummary,
)
from app.services.alert_service import AlertService
from app.services.shop_listing_sales_service import ShopListingSalesService
from app.services.shop_parser import parse_ebay_shop_url
from app.services.shop_scan_service import ShopScanService


class DuplicateShopError(Exception):
    pass


class ShopService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shop_scan_service = ShopScanService(db)
        self.alert_service = AlertService(db)
        self.sales_service = ShopListingSalesService()

    def create_shop(self, url: str, note: str | None) -> tuple[Shop, ShopScanSummary]:
        parsed = parse_ebay_shop_url(url)
        existing_shop = self.db.scalar(
            select(Shop).where(
                Shop.marketplace == parsed.marketplace,
                Shop.seller_username == parsed.seller_username,
            )
        )
        if existing_shop:
            raise DuplicateShopError

        shop = Shop(
            marketplace=parsed.marketplace,
            seller_username=parsed.seller_username,
            shop_name=parsed.shop_name,
            shop_url=parsed.normalized_url,
            note=note,
            status=ShopStatus.ACTIVE,
            scan_enabled=True,
        )
        self.db.add(shop)
        self.db.flush()
        self.alert_service.ensure_default_rules(shop)

        scan_job = self.shop_scan_service.scan_shop(shop=shop, trigger_source="CREATE_SHOP")
        self.db.commit()
        self.db.refresh(shop)

        return shop, ShopScanSummary(
            status=scan_job.status.value,
            message="Initial shop scan completed." if scan_job.status.value == "SUCCESS" else "Initial shop scan failed.",
        )

    def list_shops(self) -> list[ShopResponse]:
        shops = self.db.scalars(select(Shop).order_by(Shop.created_at.desc())).all()
        return [
            ShopResponse(
                id=shop.id,
                marketplace=shop.marketplace.value,
                seller_username=shop.seller_username,
                shop_name=shop.shop_name,
                shop_url=shop.shop_url,
                note=shop.note,
                status=shop.status.value,
                scan_enabled=shop.scan_enabled,
                last_scanned_at=shop.last_scanned_at,
                created_at=shop.created_at,
                updated_at=shop.updated_at,
                initial_scan=None,
            )
            for shop in shops
        ]

    def get_shop_detail(self, shop_id: str) -> ShopDetailResponse | None:
        shop = self.db.get(Shop, shop_id)
        if shop is None:
            return None

        recent_stats = self.db.scalars(
            select(ShopDailyStat)
            .where(ShopDailyStat.shop_id == shop.id)
            .order_by(ShopDailyStat.stat_date.desc())
            .limit(30)
        ).all()
        active_listings = self.db.scalars(
            select(ShopListing)
            .where(
                ShopListing.shop_id == shop.id,
                ShopListing.listing_status == ListingStatus.ACTIVE,
            )
            .order_by(ShopListing.updated_at.desc())
            .limit(100)
        ).all()
        self._hydrate_sales_summary(active_listings[:10])

        total_listings = self.db.scalar(
            select(func.count()).select_from(ShopListing).where(ShopListing.shop_id == shop.id)
        ) or 0
        open_alert_count = self.db.scalar(
            select(func.count()).select_from(Alert).where(
                Alert.shop_id == shop.id,
                Alert.status == AlertStatus.OPEN,
            )
        ) or 0

        last_7d_start = (recent_stats[0].stat_date - timedelta(days=6)) if recent_stats else None
        last_7d_stats = [stat for stat in recent_stats if last_7d_start and stat.stat_date >= last_7d_start]
        latest_stat = recent_stats[0] if recent_stats else None
        active_count = latest_stat.active_listing_count if latest_stat else 0
        active_ratio = Decimal("0.0000")
        if total_listings > 0:
            active_ratio = (Decimal(active_count) / Decimal(total_listings)).quantize(Decimal("0.0001"))

        portrait = ShopPortrait(
            active_listing_count=active_count,
            active_ratio=active_ratio,
            average_price=latest_stat.average_price if latest_stat else None,
            last_7d_new_count=sum(stat.new_listing_count for stat in last_7d_stats),
            last_7d_ended_count=sum(stat.ended_listing_count for stat in last_7d_stats),
            last_7d_price_drop_count=sum(stat.price_drop_count for stat in last_7d_stats),
            open_alert_count=open_alert_count,
        )

        return ShopDetailResponse(
            id=shop.id,
            marketplace=shop.marketplace.value,
            seller_username=shop.seller_username,
            shop_name=shop.shop_name,
            shop_url=shop.shop_url,
            note=shop.note,
            status=shop.status.value,
            scan_enabled=shop.scan_enabled,
            last_scanned_at=shop.last_scanned_at,
            created_at=shop.created_at,
            updated_at=shop.updated_at,
            portrait=portrait,
            recent_stats=[
                ShopDailyStatEntry(
                    id=stat.id,
                    stat_date=stat.stat_date,
                    active_listing_count=stat.active_listing_count,
                    new_listing_count=stat.new_listing_count,
                    ended_listing_count=stat.ended_listing_count,
                    price_drop_count=stat.price_drop_count,
                    price_rise_count=stat.price_rise_count,
                    average_price=stat.average_price,
                    scanned_at=stat.scanned_at,
                )
                for stat in recent_stats
            ],
            active_listings=[
                ShopListingEntry(
                    id=listing.id,
                    legacy_item_id=listing.legacy_item_id,
                    title=listing.title,
                    item_url=listing.item_url,
                    image_url=listing.image_url,
                    currency=listing.currency,
                    current_price=listing.current_price,
                    current_shipping_cost=listing.current_shipping_cost,
                    total_cost=listing.total_cost,
                    availability=listing.availability,
                    sales_summary=listing.sales_summary,
                    listing_status=listing.listing_status.value,
                    first_seen_at=listing.first_seen_at,
                    last_seen_at=listing.last_seen_at,
                    last_price_change_at=listing.last_price_change_at,
                )
                for listing in active_listings
            ],
        )

    def delete_shop(self, shop_id: str) -> bool:
        shop = self.db.get(Shop, shop_id)
        if shop is None:
            return False

        self.db.delete(shop)
        self.db.commit()
        return True

    def _hydrate_sales_summary(self, listings: list[ShopListing]) -> None:
        updated = False
        for listing in listings:
            if listing.sales_summary or not listing.item_url:
                continue
            sales_summary = self.sales_service.fetch_sales_summary(listing.item_url)
            if not sales_summary:
                continue
            listing.sales_summary = sales_summary
            updated = True

        if updated:
            self.db.commit()
