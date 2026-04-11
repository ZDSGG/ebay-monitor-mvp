from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import require_app_access
from app.core.database import get_db
from app.schemas.item import (
    BulkDeleteResponse,
    BulkDeactivateResponse,
    BulkItemActionRequest,
    BulkRefreshResponse,
    DashboardSummaryResponse,
    ItemDetailResponse,
    ItemListResponse,
    MonitoredItemCreateRequest,
    MonitoredItemResponse,
    RecentEventListResponse,
    UpdateItemNoteRequest,
)
from app.schemas.report import CsvImportResponse
from app.services.csv_import_service import CsvImportService
from app.services.item_service import DuplicateItemError, ItemService


router = APIRouter(prefix="/items", tags=["items"], dependencies=[Depends(require_app_access)])


@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    return ItemService(db=db).get_dashboard_summary()


@router.get("/recent-events", response_model=RecentEventListResponse)
def get_recent_events(
    limit: int = Query(default=8, ge=1, le=30),
    db: Session = Depends(get_db),
) -> RecentEventListResponse:
    return ItemService(db=db).get_recent_events(limit=limit)


@router.post("", response_model=MonitoredItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: MonitoredItemCreateRequest, db: Session = Depends(get_db)) -> MonitoredItemResponse:
    service = ItemService(db=db)
    try:
        item, crawl_summary = service.create_item(url=str(payload.url), note=payload.note)
    except DuplicateItemError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item already exists for the same marketplace and legacy_item_id.",
        ) from exc

    return MonitoredItemResponse(
        id=item.id,
        marketplace=item.marketplace.value,
        legacy_item_id=item.legacy_item_id,
        url=item.url,
        note=item.note,
        status=item.status.value,
        title=item.title,
        currency=item.currency,
        current_price=item.current_price,
        current_shipping_cost=item.current_shipping_cost,
        seller_name=item.seller_name,
        item_condition=item.item_condition,
        availability=item.availability,
        image_url=item.image_url,
        canonical_item_url=item.canonical_item_url,
        last_captured_at=item.last_captured_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        initial_crawl=crawl_summary,
    )


@router.get("", response_model=ItemListResponse)
def list_items(db: Session = Depends(get_db)) -> ItemListResponse:
    return ItemListResponse(items=ItemService(db=db).list_items())


@router.get("/{item_id}", response_model=ItemDetailResponse)
def get_item_detail(item_id: str, db: Session = Depends(get_db)) -> ItemDetailResponse:
    item = ItemService(db=db).get_item_detail(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    return item


@router.post("/bulk-refresh", response_model=BulkRefreshResponse)
def bulk_refresh_items(payload: BulkItemActionRequest, db: Session = Depends(get_db)) -> BulkRefreshResponse:
    return ItemService(db=db).refresh_items(item_ids=payload.item_ids)


@router.post("/bulk-deactivate", response_model=BulkDeactivateResponse)
def bulk_deactivate_items(
    payload: BulkItemActionRequest,
    db: Session = Depends(get_db),
) -> BulkDeactivateResponse:
    return ItemService(db=db).deactivate_items(item_ids=payload.item_ids)


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_items(
    payload: BulkItemActionRequest,
    db: Session = Depends(get_db),
) -> BulkDeleteResponse:
    return ItemService(db=db).delete_items(item_ids=payload.item_ids)


@router.post("/{item_id}/refresh", response_model=BulkRefreshResponse)
def refresh_single_item(item_id: str, db: Session = Depends(get_db)) -> BulkRefreshResponse:
    return ItemService(db=db).refresh_items(item_ids=[UUID(item_id)])


@router.patch("/{item_id}/note", response_model=MonitoredItemResponse)
def update_item_note(
    item_id: str,
    payload: UpdateItemNoteRequest,
    db: Session = Depends(get_db),
) -> MonitoredItemResponse:
    service = ItemService(db=db)
    item = service.update_item_note(item_id=item_id, note=payload.note)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    return MonitoredItemResponse(
        id=item.id,
        marketplace=item.marketplace.value,
        legacy_item_id=item.legacy_item_id,
        url=item.url,
        note=item.note,
        status=item.status.value,
        title=item.title,
        currency=item.currency,
        current_price=item.current_price,
        current_shipping_cost=item.current_shipping_cost,
        seller_name=item.seller_name,
        item_condition=item.item_condition,
        availability=item.availability,
        image_url=item.image_url,
        canonical_item_url=item.canonical_item_url,
        last_captured_at=item.last_captured_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        initial_crawl={"status": "SUCCESS", "message": "Note updated."},
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)) -> None:
    deleted = ItemService(db=db).delete_item(item_id=item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")


@router.post("/import-csv", response_model=CsvImportResponse)
async def import_items_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> CsvImportResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported.")

    content = await file.read()
    result = CsvImportService(db).import_items(content)
    return CsvImportResponse(**result)
