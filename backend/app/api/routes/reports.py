from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.report_service import ReportService


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/items/{item_id}/export")
def export_item_report(item_id: str, db: Session = Depends(get_db)) -> StreamingResponse:
    content, filename = ReportService(db).export_item_excel(item_id)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
