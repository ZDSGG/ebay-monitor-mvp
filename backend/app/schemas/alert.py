from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AlertEntry(BaseModel):
    id: UUID
    shop_id: UUID | None
    shop_name: str | None
    seller_username: str | None
    alert_rule_id: UUID | None
    alert_type: str
    severity: str
    status: str
    title: str
    message: str
    triggered_at: datetime
    resolved_at: datetime | None
    payload_json: dict | None


class AlertListResponse(BaseModel):
    alerts: list[AlertEntry]


class AlertResolveResponse(BaseModel):
    id: UUID
    status: str
    resolved_at: datetime | None


class AlertRuleEntry(BaseModel):
    id: UUID
    shop_id: UUID | None
    shop_name: str | None
    rule_name: str
    rule_type: str
    threshold_value: Decimal | None
    threshold_unit: str | None
    is_enabled: bool
    description: str | None
    params_json: dict | None
    created_at: datetime
    updated_at: datetime


class AlertRuleListResponse(BaseModel):
    rules: list[AlertRuleEntry]
