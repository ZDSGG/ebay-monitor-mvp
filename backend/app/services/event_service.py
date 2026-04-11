from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import EventType
from app.models.item_event import ItemEvent
from app.models.item_snapshot import ItemSnapshot
from app.models.monitored_item import MonitoredItem


@dataclass(slots=True)
class EventAnalysisResult:
    previous_price: Decimal | None
    current_price: Decimal
    diff_amount: Decimal | None
    diff_rate: Decimal | None
    event_type: EventType | None


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyze_and_record_events(self, item: MonitoredItem, current_snapshot: ItemSnapshot) -> list[ItemEvent]:
        created_events: list[ItemEvent] = []
        compare_windows = {
            "1d": timedelta(days=1),
            "7d": timedelta(days=7),
        }

        for compare_window, delta in compare_windows.items():
            previous_snapshot = self.db.scalar(
                select(ItemSnapshot)
                .where(
                    ItemSnapshot.item_id == item.id,
                    ItemSnapshot.capture_time <= current_snapshot.capture_time - delta,
                )
                .order_by(ItemSnapshot.capture_time.desc())
                .limit(1)
            )
            if previous_snapshot is None:
                continue

            result = self._analyze_prices(
                current_price=current_snapshot.price,
                previous_price=previous_snapshot.price,
            )
            if result.event_type is None:
                continue

            event = ItemEvent(
                item_id=item.id,
                event_type=result.event_type,
                compare_window=compare_window,
                previous_price=result.previous_price,
                current_price=result.current_price,
                diff_amount=result.diff_amount,
                diff_rate=result.diff_rate,
                event_time=current_snapshot.capture_time,
            )
            self.db.add(event)
            created_events.append(event)

        self.db.flush()
        return created_events

    def _analyze_prices(self, current_price: Decimal, previous_price: Decimal) -> EventAnalysisResult:
        diff = (current_price - previous_price).quantize(Decimal("0.01"))
        if abs(diff) < Decimal("0.01"):
            return EventAnalysisResult(
                previous_price=previous_price,
                current_price=current_price,
                diff_amount=Decimal("0.00"),
                diff_rate=Decimal("0.0000"),
                event_type=EventType.NO_CHANGE,
            )

        diff_rate = None
        if previous_price != Decimal("0"):
            diff_rate = (diff / previous_price).quantize(Decimal("0.0001"))

        event_type = EventType.PRICE_DROP if diff < 0 else EventType.PRICE_RISE
        return EventAnalysisResult(
            previous_price=previous_price,
            current_price=current_price,
            diff_amount=diff,
            diff_rate=diff_rate,
            event_type=event_type,
        )
