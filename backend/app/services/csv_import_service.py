import csv
from io import StringIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.item_service import DuplicateItemError, ItemService


class CsvImportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.item_service = ItemService(db)

    def import_items(self, content: bytes) -> dict:
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must be UTF-8 encoded.",
            ) from exc

        reader = csv.DictReader(StringIO(decoded))
        if not reader.fieldnames or "url" not in reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must include a 'url' column.",
            )

        results: list[dict] = []
        created_count = 0
        skipped_count = 0
        failed_count = 0

        for row in reader:
            url = (row.get("url") or "").strip()
            note = (row.get("note") or "").strip() or None
            if not url:
                failed_count += 1
                results.append(
                    {
                        "url": "",
                        "note": note,
                        "status": "FAILED",
                        "item_id": None,
                        "message": "Missing URL.",
                    }
                )
                continue

            try:
                item, crawl_summary = self.item_service.create_item(url=url, note=note)
                created_count += 1
                results.append(
                    {
                        "url": url,
                        "note": note,
                        "status": "CREATED",
                        "item_id": str(item.id),
                        "message": crawl_summary.message,
                    }
                )
            except DuplicateItemError:
                self.db.rollback()
                skipped_count += 1
                results.append(
                    {
                        "url": url,
                        "note": note,
                        "status": "SKIPPED",
                        "item_id": None,
                        "message": "Duplicate marketplace + legacy_item_id.",
                    }
                )
            except Exception as exc:
                self.db.rollback()
                failed_count += 1
                results.append(
                    {
                        "url": url,
                        "note": note,
                        "status": "FAILED",
                        "item_id": None,
                        "message": str(exc),
                    }
                )

        return {
            "total_rows": len(results),
            "created_count": created_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "results": results,
        }
