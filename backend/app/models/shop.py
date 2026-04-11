import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.models.base import Base
from app.models.enums import Marketplace, ShopStatus


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (UniqueConstraint("marketplace", "seller_username", name="uq_shop_marketplace_seller"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marketplace: Mapped[Marketplace] = mapped_column(Enum(Marketplace, name="marketplace_enum"), nullable=False, index=True)
    seller_username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    shop_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shop_url: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ShopStatus] = mapped_column(
        Enum(ShopStatus, name="shop_status_enum"),
        nullable=False,
        default=ShopStatus.ACTIVE,
        index=True,
    )
    scan_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    listings = relationship("ShopListing", back_populates="shop", cascade="all, delete-orphan")
    daily_stats = relationship("ShopDailyStat", back_populates="shop", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="shop", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="shop", cascade="all, delete-orphan")
    crawl_jobs = relationship("CrawlJob", back_populates="shop")
