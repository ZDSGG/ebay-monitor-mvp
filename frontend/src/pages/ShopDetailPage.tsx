import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { StatusPill } from "../components/StatusPill";
import { deleteShop, getAlertRules, getAlerts, getShopDetail, scanShop } from "../lib/api";
import { formatMoney, formatPercent, formatUtc } from "../lib/format";
import type { AlertEntry, AlertRuleEntry, ShopDetailResponse } from "../types";

function getSeverityTone(severity: string) {
  if (severity === "HIGH") return "drop";
  if (severity === "MEDIUM") return "rise";
  return "neutral";
}

export function ShopDetailPage() {
  const { shopId = "" } = useParams();
  const navigate = useNavigate();
  const [shop, setShop] = useState<ShopDetailResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [rules, setRules] = useState<AlertRuleEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadShopData() {
    const [detail, alertResponse, ruleResponse] = await Promise.all([
      getShopDetail(shopId),
      getAlerts({ shopId, limit: 20 }),
      getAlertRules(shopId),
    ]);
    setShop(detail);
    setAlerts(alertResponse.alerts);
    setRules(ruleResponse.rules);
  }

  useEffect(() => {
    loadShopData()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [shopId]);

  const statChartData = useMemo(
    () =>
      (shop?.recent_stats ?? [])
        .slice()
        .reverse()
        .map((stat) => ({
          date: new Date(stat.stat_date).toLocaleDateString("zh-CN", { month: "numeric", day: "numeric", timeZone: "UTC" }),
          在售: stat.active_listing_count,
          新增: stat.new_listing_count,
          下架: stat.ended_listing_count,
          降价: stat.price_drop_count,
        })),
    [shop],
  );

  async function handleScan() {
    if (!shop) {
      return;
    }
    setScanning(true);
    setError(null);
    setMessage(null);
    try {
      const result = await scanShop(shop.id);
      await loadShopData();
      setMessage(`店铺扫描完成，成功 ${result.succeeded}，失败 ${result.failed}。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "店铺扫描失败。");
    } finally {
      setScanning(false);
    }
  }

  async function handleDelete() {
    if (!shop) {
      return;
    }
    const confirmed = window.confirm(`确认移除店铺监控“${shop.shop_name}”吗？相关店铺数据会一起删除。`);
    if (!confirmed) {
      return;
    }
    try {
      await deleteShop(shop.id);
      navigate("/shops");
    } catch (err) {
      setError(err instanceof Error ? err.message : "店铺移除失败。");
    }
  }

  if (loading) return <div className="empty-panel">正在加载店铺详情...</div>;
  if (error) return <div className="empty-panel error-panel">{error}</div>;
  if (!shop) return <div className="empty-panel">未找到店铺。</div>;

  return (
    <section className="workspace-stack">
      {message ? <div className="notice-banner success-panel">{message}</div> : null}

      <div className="detail-hero">
        <div className="detail-copy">
          <p className="eyebrow">{shop.marketplace}</p>
          <h2>{shop.shop_name}</h2>
          <p className="muted-note">
            @{shop.seller_username} | 最近扫描 {formatUtc(shop.last_scanned_at)}
          </p>
          <div className="detail-meta">
            <div>
              <span>当前在售</span>
              <strong>{shop.portrait.active_listing_count}</strong>
            </div>
            <div>
              <span>活跃占比</span>
              <strong>{formatPercent(shop.portrait.active_ratio, false)}</strong>
            </div>
            <div>
              <span>平均价格</span>
              <strong>{formatMoney(shop.portrait.average_price, shop.active_listings[0]?.currency ?? "USD")}</strong>
            </div>
          </div>
        </div>
        <div className="shop-summary-panel">
          <div className="tag-stack">
            <StatusPill tone={shop.status === "ACTIVE" ? "rise" : "neutral"}>{shop.status === "ACTIVE" ? "监控中" : "已停用"}</StatusPill>
            <StatusPill tone={shop.portrait.open_alert_count > 0 ? "drop" : "neutral"}>
              未处理预警 {shop.portrait.open_alert_count}
            </StatusPill>
          </div>
          <div className="row-actions">
            <button className="primary-button" type="button" onClick={handleScan} disabled={scanning}>
              {scanning ? "扫描中..." : "立即扫描店铺"}
            </button>
            <a className="action-link" href={shop.shop_url} target="_blank" rel="noreferrer">
              打开店铺
            </a>
            <Link className="action-link" to="/alerts">
              打开预警中心
            </Link>
            <button className="action-link" type="button" onClick={handleDelete}>
              移除监控
            </button>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>近 7 天新增</span>
          <strong>{shop.portrait.last_7d_new_count}</strong>
          <p>监控上新节奏。</p>
        </div>
        <div className="stat-card">
          <span>近 7 天下架</span>
          <strong>{shop.portrait.last_7d_ended_count}</strong>
          <p>监控下架和清仓动作。</p>
        </div>
        <div className="stat-card">
          <span>近 7 天降价</span>
          <strong>{shop.portrait.last_7d_price_drop_count}</strong>
          <p>识别促销和竞争压力。</p>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="chart-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">店铺日统计</p>
              <h3>近 30 天商品变化</h3>
            </div>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={statChartData}>
                <CartesianGrid stroke="rgba(147, 197, 253, 0.08)" vertical={false} />
                <XAxis dataKey="date" stroke="#6b7a90" />
                <YAxis stroke="#6b7a90" />
                <Tooltip
                  contentStyle={{
                    background: "#0f1723",
                    border: "1px solid rgba(148, 163, 184, 0.2)",
                    borderRadius: 16,
                  }}
                />
                <Bar dataKey="在售" fill="#7dd3fc" radius={[6, 6, 0, 0]} />
                <Bar dataKey="新增" fill="#54e7c5" radius={[6, 6, 0, 0]} />
                <Bar dataKey="下架" fill="#ff7a90" radius={[6, 6, 0, 0]} />
                <Bar dataKey="降价" fill="#fbbf24" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="event-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">店铺规则</p>
              <h3>预警规则</h3>
            </div>
          </div>
          <div className="anomaly-list">
            {rules.map((rule) => (
              <div key={rule.id} className="anomaly-row">
                <div className="anomaly-row-main">
                  <StatusPill tone={rule.is_enabled ? "rise" : "neutral"}>{rule.is_enabled ? "启用" : "停用"}</StatusPill>
                  <div>
                    <strong>{rule.rule_name}</strong>
                    <p>{rule.description ?? rule.rule_type}</p>
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
            {rules.length === 0 ? <div className="empty-inline">暂无规则。</div> : null}
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="table-shell">
          <div className="section-head">
            <div>
              <p className="eyebrow">活跃商品</p>
              <h3>当前在售列表</h3>
            </div>
          </div>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>商品</th>
                  <th>价格</th>
                  <th>运费</th>
                  <th>总价</th>
                  <th>销量明细</th>
                  <th>最近出现</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {shop.active_listings.map((listing) => (
                  <tr key={listing.id}>
                    <td>
                      <div className="item-main">
                        <strong>{listing.title}</strong>
                        <p className="muted-row">ID {listing.legacy_item_id}</p>
                      </div>
                    </td>
                    <td>{formatMoney(listing.current_price, listing.currency ?? "USD")}</td>
                    <td>{formatMoney(listing.current_shipping_cost, listing.currency ?? "USD")}</td>
                    <td>{formatMoney(listing.total_cost, listing.currency ?? "USD")}</td>
                    <td>{listing.sales_summary ?? "--"}</td>
                    <td>{formatUtc(listing.last_seen_at)}</td>
                    <td>
                      <a className="table-action" href={listing.item_url} target="_blank" rel="noreferrer">
                        打开商品
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {shop.active_listings.length === 0 ? <div className="empty-inline">当前没有在售商品。</div> : null}
          </div>
        </div>

        <div className="log-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">近期预警</p>
              <h3>未处理与历史事件</h3>
            </div>
          </div>
          <div className="event-list">
            {alerts.map((alert) => (
              <div key={alert.id} className="event-row">
                <StatusPill tone={getSeverityTone(alert.severity)}>{alert.severity}</StatusPill>
                <div>
                  <strong>{alert.title}</strong>
                  <p>{alert.message}</p>
                </div>
                <div>
                  <strong>{alert.status}</strong>
                  <p>{formatUtc(alert.triggered_at)}</p>
                </div>
              </div>
            ))}
            {alerts.length === 0 ? <div className="empty-inline">当前没有预警。</div> : null}
          </div>
        </div>
      </div>
    </section>
  );
}
