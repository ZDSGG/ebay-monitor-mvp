from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_app_access
from app.core.database import get_db
from app.models.enums import JobStatus
from app.models.shop import Shop
from app.schemas.ops import CrawlTriggerResponse
from app.schemas.shop import ShopCreateRequest, ShopDetailResponse, ShopResponse
from app.services.shop_service import DuplicateShopError, ShopService
from app.services.shop_scan_service import ShopScanService


router = APIRouter(prefix="/shops", tags=["shops"], dependencies=[Depends(require_app_access)])


@router.post("", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
def create_shop(payload: ShopCreateRequest, db: Session = Depends(get_db)) -> ShopResponse:
    service = ShopService(db=db)
    try:
        shop, initial_scan = service.create_shop(url=str(payload.url), note=payload.note)
    except DuplicateShopError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Shop already exists for the same marketplace and seller username.",
        ) from exc

    return ShopResponse(
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
        initial_scan=initial_scan,
    )


@router.get("", response_model=list[ShopResponse])
def list_shops(db: Session = Depends(get_db)) -> list[ShopResponse]:
    return ShopService(db=db).list_shops()


@router.get("/{shop_id}", response_model=ShopDetailResponse)
def get_shop_detail(shop_id: str, db: Session = Depends(get_db)) -> ShopDetailResponse:
    shop = ShopService(db=db).get_shop_detail(shop_id)
    if shop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")
    return shop


@router.post("/{shop_id}/scan", response_model=CrawlTriggerResponse)
def scan_single_shop(shop_id: str, db: Session = Depends(get_db)) -> CrawlTriggerResponse:
    shop = db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")

    job = ShopScanService(db).scan_shop(shop=shop, trigger_source="MANUAL")
    db.commit()
    return CrawlTriggerResponse(
        requested=1,
        succeeded=1 if job.status == JobStatus.SUCCESS else 0,
        failed=1 if job.status == JobStatus.FAILED else 0,
        trigger_source="MANUAL",
    )
