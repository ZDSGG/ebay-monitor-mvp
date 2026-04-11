from io import BytesIO

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item_event import ItemEvent
from app.models.item_snapshot import ItemSnapshot
from app.models.monitored_item import MonitoredItem


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def export_item_excel(self, item_id: str) -> tuple[bytes, str]:
        item = self.db.get(MonitoredItem, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

        snapshots = self.db.scalars(
            select(ItemSnapshot)
            .where(ItemSnapshot.item_id == item.id)
            .order_by(ItemSnapshot.capture_time.asc())
        ).all()
        events = self.db.scalars(
            select(ItemEvent)
            .where(ItemEvent.item_id == item.id)
            .order_by(ItemEvent.event_time.desc())
        ).all()

        summary_df = pd.DataFrame(
            [
                {
                    "item_id": str(item.id),
                    "marketplace": item.marketplace.value,
                    "legacy_item_id": item.legacy_item_id,
                    "title": item.title,
                    "url": item.url,
                    "note": item.note,
                    "status": item.status.value,
                    "currency": item.currency,
                    "current_price": float(item.current_price) if item.current_price is not None else None,
                    "current_shipping_cost": float(item.current_shipping_cost) if item.current_shipping_cost is not None else None,
                    "seller_name": item.seller_name,
                    "item_condition": item.item_condition,
                    "availability": item.availability,
                    "last_captured_at_utc": item.last_captured_at.isoformat() if item.last_captured_at else None,
                }
            ]
        )
        snapshot_df = pd.DataFrame(
            [
                {
                    "capture_time_utc": snapshot.capture_time.isoformat(),
                    "price": float(snapshot.price),
                    "shipping_cost": float(snapshot.shipping_cost),
                    "total_cost": float(snapshot.total_cost),
                }
                for snapshot in snapshots
            ]
        )
        events_df = pd.DataFrame(
            [
                {
                    "event_time_utc": event.event_time.isoformat(),
                    "event_type": event.event_type.value,
                    "compare_window": event.compare_window,
                    "previous_price": float(event.previous_price) if event.previous_price is not None else None,
                    "current_price": float(event.current_price),
                    "diff_amount": float(event.diff_amount) if event.diff_amount is not None else None,
                    "diff_rate": float(event.diff_rate) if event.diff_rate is not None else None,
                }
                for event in events
            ]
        )

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary_df.to_excel(writer, index=False, sheet_name="Summary")
            snapshot_df.to_excel(writer, index=False, sheet_name="Daily Data")
            events_df.to_excel(writer, index=False, sheet_name="Event Log")

        filename = f"item_report_{item.legacy_item_id}.xlsx"
        return output.getvalue(), filename
