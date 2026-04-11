import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.models.base import Base


class ShopDailyStat(Base):
    __tablename__ = "shop_daily_stats"
    __table_args__ = (UniqueConstraint("shop_id", "stat_date", name="uq_shop_daily_stat"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    active_listing_count: Mapped[int] = mapped_column(nullable=False, default=0)
    new_listing_count: Mapped[int] = mapped_column(nullable=False, default=0)
    ended_listing_count: Mapped[int] = mapped_column(nullable=False, default=0)
    price_drop_count: Mapped[int] = mapped_column(nullable=False, default=0)
    price_rise_count: Mapped[int] = mapped_column(nullable=False, default=0)
    average_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    shop = relationship("Shop", back_populates="daily_stats")
