from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_app_access
from app.core.database import get_db
from app.schemas.alert import AlertListResponse, AlertResolveResponse, AlertRuleListResponse
from app.services.alert_service import AlertService


router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(require_app_access)])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    shop_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    return AlertService(db).list_alerts(status_filter=status_filter, shop_id=shop_id, limit=limit)


@router.get("/rules", response_model=AlertRuleListResponse)
def list_alert_rules(
    shop_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AlertRuleListResponse:
    return AlertService(db).list_rules(shop_id=shop_id)


@router.patch("/{alert_id}/resolve", response_model=AlertResolveResponse)
def resolve_alert(alert_id: str, db: Session = Depends(get_db)) -> AlertResolveResponse:
    resolved = AlertService(db).resolve_alert(alert_id)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return resolved
