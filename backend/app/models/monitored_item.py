import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.models.base import Base
from app.models.enums import ItemStatus, Marketplace


class MonitoredItem(Base):
    __tablename__ = "monitored_items"
    __table_args__ = (
        UniqueConstraint("marketplace", "legacy_item_id", name="uq_marketplace_item_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marketplace: Mapped[Marketplace] = mapped_column(
        Enum(Marketplace, name="marketplace_enum"),
        nullable=False,
        index=True,
    )
    legacy_item_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, name="item_status_enum"),
        nullable=False,
        default=ItemStatus.ACTIVE,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    current_shipping_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    seller_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_condition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_item_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    snapshots = relationship("ItemSnapshot", back_populates="item", cascade="all, delete-orphan")
    events = relationship("ItemEvent", back_populates="item", cascade="all, delete-orphan")
    crawl_jobs = relationship("CrawlJob", back_populates="item", cascade="all, delete-orphan")
