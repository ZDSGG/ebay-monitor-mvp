from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.item_snapshot import ItemSnapshot
from app.models.monitored_item import MonitoredItem


class SnapshotService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_snapshot(
        self,
        item: MonitoredItem,
        price: Decimal,
        shipping_cost: Decimal,
        capture_time=None,
    ) -> ItemSnapshot:
        snapshot = ItemSnapshot(
            item_id=item.id,
            price=price,
            shipping_cost=shipping_cost,
            total_cost=price + shipping_cost,
            capture_time=capture_time or utc_now(),
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot
