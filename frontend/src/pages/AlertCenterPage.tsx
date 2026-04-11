import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { StatusPill } from "../components/StatusPill";
import { getAlerts, getAlertRules, getShops, resolveAlert } from "../lib/api";
import { formatUtc } from "../lib/format";
import type { AlertEntry, AlertRuleEntry, ShopResponse } from "../types";

function getSeverityTone(severity: string) {
  if (severity === "HIGH") return "drop";
  if (severity === "MEDIUM") return "rise";
  return "neutral";
}

export function AlertCenterPage() {
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [rules, setRules] = useState<AlertRuleEntry[]>([]);
  const [shops, setShops] = useState<ShopResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("OPEN");
  const [shopFilter, setShopFilter] = useState("ALL");
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  async function loadAlertCenter(status = statusFilter, shopId = shopFilter) {
    const [alertResponse, ruleResponse, shopResponse] = await Promise.all([
      getAlerts({
        status: status === "ALL" ? undefined : status,
        shopId: shopId === "ALL" ? undefined : shopId,
        limit: 100,
      }),
      getAlertRules(shopId === "ALL" ? undefined : shopId),
      getShops(),
    ]);
    setAlerts(alertResponse.alerts);
    setRules(ruleResponse.rules);
    setShops(shopResponse);
  }

  useEffect(() => {
    loadAlertCenter()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (loading) return;
    loadAlertCenter(statusFilter, shopFilter).catch((err: Error) => setError(err.message));
  }, [statusFilter, shopFilter]);

  const openCount = useMemo(() => alerts.filter((alert) => alert.status === "OPEN").length, [alerts]);
  const highCount = useMemo(() => alerts.filter((alert) => alert.severity === "HIGH").length, [alerts]);

  async function handleResolve(alert: AlertEntry) {
    setResolvingId(alert.id);
    setError(null);
    setMessage(null);
    try {
      await resolveAlert(alert.id);
      await loadAlertCenter(statusFilter, shopFilter);
      setMessage(`预警「${alert.title}」已标记为已处理。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "预警处理失败。");
    } finally {
      setResolvingId(null);
    }
  }

  if (loading) {
    return <div className="empty-panel">正在加载预警中心...</div>;
  }

  return (
    <section className="workspace-stack">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">预警中心</p>
          <h2>店铺预警看板</h2>
          <p className="workspace-copy">集中查看规则命中结果、按店铺筛选、快速处理预警。</p>
        </div>
      </div>

      {message ? <div className="notice-banner success-panel">{message}</div> : null}
      {error ? <div className="notice-banner error-panel">{error}</div> : null}

      <div className="stats-grid">
        <div className="stat-card">
          <span>当前预警数</span>
          <strong>{alerts.length}</strong>
          <p>按当前筛选条件统计。</p>
        </div>
        <div className="stat-card">
          <span>未处理</span>
          <strong>{openCount}</strong>
          <p>仍需人工确认与跟进。</p>
        </div>
        <div className="stat-card">
          <span>高优先级</span>
          <strong>{highCount}</strong>
          <p>建议优先查看的高风险事件。</p>
        </div>
        <div className="stat-card">
          <span>规则总数</span>
          <strong>{rules.length}</strong>
          <p>当前已生效的规则模板。</p>
        </div>
      </div>

      <div className="filter-panel">
        <div className="filter-row">
          <label className="filter-field">
            <span>预警状态</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="OPEN">未处理</option>
              <option value="RESOLVED">已处理</option>
              <option value="ALL">全部</option>
            </select>
          </label>
          <label className="filter-field">
            <span>店铺</span>
            <select value={shopFilter} onChange={(event) => setShopFilter(event.target.value)}>
              <option value="ALL">全部店铺</option>
              {shops.map((shop) => (
                <option key={shop.id} value={shop.id}>
                  {shop.shop_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="table-shell">
          <div className="section-head">
            <div>
              <p className="eyebrow">预警列表</p>
              <h3>规则命中事件</h3>
            </div>
          </div>
          <div className="alert-list">
            {alerts.map((alert) => (
              <div key={alert.id} className="alert-card">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">{alert.alert_type}</p>
                    <h3>{alert.title}</h3>
                  </div>
                  <div className="tag-stack">
                    <StatusPill tone={getSeverityTone(alert.severity)}>{alert.severity}</StatusPill>
                    <StatusPill tone={alert.status === "OPEN" ? "drop" : "neutral"}>{alert.status}</StatusPill>
                  </div>
                </div>
                <p className="muted-note">{alert.message}</p>
                <div className="drawer-meta">
                  <span>店铺 {alert.shop_name ?? "--"}</span>
                  <span>卖家 @{alert.seller_username ?? "--"}</span>
                  <span>触发时间 {formatUtc(alert.triggered_at)}</span>
                </div>
                <div className="row-actions">
                  {alert.shop_id ? (
                    <Link className="table-action" to={`/shops/${alert.shop_id}`}>
                      查看店铺
                    </Link>
                  ) : null}
                  {alert.status === "OPEN" ? (
                    <button
                      className="table-action"
                      type="button"
                      disabled={resolvingId === alert.id}
                      onClick={() => handleResolve(alert)}
                    >
                      {resolvingId === alert.id ? "处理中..." : "标记已处理"}
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
            {alerts.length === 0 ? <div className="empty-inline">当前没有预警数据。</div> : null}
          </div>
        </div>

        <div className="event-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">规则列表</p>
              <h3>店铺规则总览</h3>
            </div>
          </div>
          <div className="anomaly-list">
            {rules.map((rule) => (
              <div key={rule.id} className="anomaly-row">
                <div className="anomaly-row-main">
                  <StatusPill tone={rule.is_enabled ? "rise" : "neutral"}>{rule.is_enabled ? "启用" : "停用"}</StatusPill>
                  <div>
                    <strong>{rule.rule_name}</strong>
                    <p>{rule.shop_name ?? "全局规则"}</p>
                  </div>
                </div>
                <div className="anomaly-row-meta">
                  <strong>
                    {rule.threshold_value ?? "--"} {rule.threshold_unit ?? ""}
                  </strong>
                  <span>{rule.rule_type}</span>
                </div>
              </div>
            ))}
            {rules.length === 0 ? <div className="empty-inline">暂无规则数据。</div> : null}
          </div>
        </div>
      </div>
    </section>
  );
}
