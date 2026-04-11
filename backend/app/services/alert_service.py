from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.time import utc_now
from app.models.alert import Alert
from app.models.alert_rule import AlertRule
from app.models.enums import AlertRuleType, AlertSeverity, AlertStatus
from app.models.shop import Shop
from app.models.shop_daily_stat import ShopDailyStat
from app.schemas.alert import AlertEntry, AlertListResponse, AlertResolveResponse, AlertRuleEntry, AlertRuleListResponse


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_default_rules(self, shop: Shop) -> None:
        existing_types = {
            rule.rule_type
            for rule in self.db.scalars(select(AlertRule).where(AlertRule.shop_id == shop.id)).all()
        }

        defaults = [
            (
                AlertRuleType.NEW_LISTING_SPIKE,
                "新增商品激增",
                Decimal("5"),
                "count",
                "单日新增商品数达到阈值时触发。",
            ),
            (
                AlertRuleType.DELISTED_SPIKE,
                "下架商品激增",
                Decimal("5"),
                "count",
                "单日下架商品数达到阈值时触发。",
            ),
            (
                AlertRuleType.PRICE_DROP_SPIKE,
                "降价商品激增",
                Decimal("5"),
                "count",
                "单日降价商品数达到阈值时触发。",
            ),
            (
                AlertRuleType.ACTIVE_LISTING_DROP,
                "在售数明显下降",
                Decimal("20"),
                "percent",
                "当日较上一日的在售数量下降比例达到阈值时触发。",
            ),
        ]

        for rule_type, name, threshold, unit, description in defaults:
            if rule_type in existing_types:
                continue
            self.db.add(
                AlertRule(
                    shop_id=shop.id,
                    rule_name=name,
                    rule_type=rule_type,
                    threshold_value=threshold,
                    threshold_unit=unit,
                    is_enabled=True,
                    description=description,
                )
            )

    def evaluate_shop_rules(self, shop: Shop, current_stat: ShopDailyStat) -> None:
        rules = self.db.scalars(
            select(AlertRule).where(
                AlertRule.shop_id == shop.id,
                AlertRule.is_enabled.is_(True),
            )
        ).all()

        previous_stat = self.db.scalar(
            select(ShopDailyStat)
            .where(
                ShopDailyStat.shop_id == shop.id,
                ShopDailyStat.stat_date < current_stat.stat_date,
            )
            .order_by(ShopDailyStat.stat_date.desc())
            .limit(1)
        )

        for rule in rules:
            title: str | None = None
            message: str | None = None
            severity = AlertSeverity.MEDIUM
            payload: dict | None = None
            threshold = rule.threshold_value or Decimal("0")

            if rule.rule_type == AlertRuleType.NEW_LISTING_SPIKE and current_stat.new_listing_count >= int(threshold):
                title = f"{shop.shop_name} 新增商品异常"
                message = f"单日新增商品 {current_stat.new_listing_count} 个，达到规则阈值 {threshold}。"
                payload = {"value": current_stat.new_listing_count, "threshold": str(threshold), "stat_date": str(current_stat.stat_date)}
            elif rule.rule_type == AlertRuleType.DELISTED_SPIKE and current_stat.ended_listing_count >= int(threshold):
                title = f"{shop.shop_name} 下架商品异常"
                message = f"单日下架商品 {current_stat.ended_listing_count} 个，达到规则阈值 {threshold}。"
                severity = AlertSeverity.HIGH
                payload = {"value": current_stat.ended_listing_count, "threshold": str(threshold), "stat_date": str(current_stat.stat_date)}
            elif rule.rule_type == AlertRuleType.PRICE_DROP_SPIKE and current_stat.price_drop_count >= int(threshold):
                title = f"{shop.shop_name} 降价动作活跃"
                message = f"单日降价商品 {current_stat.price_drop_count} 个，达到规则阈值 {threshold}。"
                payload = {"value": current_stat.price_drop_count, "threshold": str(threshold), "stat_date": str(current_stat.stat_date)}
            elif rule.rule_type == AlertRuleType.ACTIVE_LISTING_DROP and previous_stat and previous_stat.active_listing_count > 0:
                delta = previous_stat.active_listing_count - current_stat.active_listing_count
                if delta > 0:
                    drop_rate = (Decimal(delta) / Decimal(previous_stat.active_listing_count) * Decimal("100")).quantize(Decimal("0.01"))
                    if drop_rate >= threshold:
                        title = f"{shop.shop_name} 在售数量下降"
                        message = (
                            f"在售数从 {previous_stat.active_listing_count} 下降到 {current_stat.active_listing_count}，"
                            f"下降 {drop_rate}% ，达到规则阈值 {threshold}% 。"
                        )
                        severity = AlertSeverity.HIGH
                        payload = {
                            "previous": previous_stat.active_listing_count,
                            "current": current_stat.active_listing_count,
                            "drop_rate": str(drop_rate),
                            "threshold": str(threshold),
                            "stat_date": str(current_stat.stat_date),
                        }

            if title and message:
                self._create_alert_if_needed(
                    shop=shop,
                    rule=rule,
                    severity=severity,
                    title=title,
                    message=message,
                    payload=payload,
                )

    def list_alerts(self, status_filter: str | None = None, shop_id: str | None = None, limit: int = 100) -> AlertListResponse:
        stmt: Select = select(Alert, Shop).join(Shop, Shop.id == Alert.shop_id, isouter=True).order_by(Alert.triggered_at.desc()).limit(limit)

        if status_filter:
            try:
                stmt = stmt.where(Alert.status == AlertStatus(status_filter))
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported alert status filter.",
                ) from exc
        if shop_id:
            stmt = stmt.where(Alert.shop_id == shop_id)

        rows = self.db.execute(stmt).all()
        return AlertListResponse(
            alerts=[
                AlertEntry(
                    id=alert.id,
                    shop_id=alert.shop_id,
                    shop_name=shop.shop_name if shop else None,
                    seller_username=shop.seller_username if shop else None,
                    alert_rule_id=alert.alert_rule_id,
                    alert_type=alert.alert_type,
                    severity=alert.severity.value,
                    status=alert.status.value,
                    title=alert.title,
                    message=alert.message,
                    triggered_at=alert.triggered_at,
                    resolved_at=alert.resolved_at,
                    payload_json=alert.payload_json,
                )
                for alert, shop in rows
            ]
        )

    def list_rules(self, shop_id: str | None = None) -> AlertRuleListResponse:
        stmt: Select = select(AlertRule, Shop).join(Shop, Shop.id == AlertRule.shop_id, isouter=True).order_by(AlertRule.created_at.desc())
        if shop_id:
            stmt = stmt.where(AlertRule.shop_id == shop_id)

        rows = self.db.execute(stmt).all()
        return AlertRuleListResponse(
            rules=[
                AlertRuleEntry(
                    id=rule.id,
                    shop_id=rule.shop_id,
                    shop_name=shop.shop_name if shop else None,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type.value,
                    threshold_value=rule.threshold_value,
                    threshold_unit=rule.threshold_unit,
                    is_enabled=rule.is_enabled,
                    description=rule.description,
                    params_json=rule.params_json,
                    created_at=rule.created_at,
                    updated_at=rule.updated_at,
                )
                for rule, shop in rows
            ]
        )

    def resolve_alert(self, alert_id: str) -> AlertResolveResponse | None:
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = utc_now()
        self.db.commit()
        self.db.refresh(alert)
        return AlertResolveResponse(id=alert.id, status=alert.status.value, resolved_at=alert.resolved_at)

    def _create_alert_if_needed(
        self,
        shop: Shop,
        rule: AlertRule,
        severity: AlertSeverity,
        title: str,
        message: str,
        payload: dict | None,
    ) -> None:
        day_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        existing = self.db.scalar(
            select(Alert).where(
                Alert.shop_id == shop.id,
                Alert.alert_rule_id == rule.id,
                Alert.status == AlertStatus.OPEN,
                Alert.triggered_at >= day_start,
            )
        )
        if existing:
            return

        self.db.add(
            Alert(
                shop_id=shop.id,
                alert_rule_id=rule.id,
                alert_type=rule.rule_type.value,
                severity=severity,
                status=AlertStatus.OPEN,
                title=title,
                message=message,
                payload_json=payload,
            )
        )
