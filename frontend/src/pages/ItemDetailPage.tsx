import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PriceHistoryChart } from "../components/PriceHistoryChart";
import { StatusPill } from "../components/StatusPill";
import { getItemDetail, getItemExportUrl } from "../lib/api";
import { formatMoney, formatPercent, formatUtc } from "../lib/format";
import { getCompareWindowLabel, getEventTone, getPriceChangeLabel } from "../lib/itemLabels";
import type { ItemDetailResponse } from "../types";

export function ItemDetailPage() {
  const { itemId = "" } = useParams();
  const [item, setItem] = useState<ItemDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getItemDetail(itemId)
      .then((data) => setItem(data))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [itemId]);

  if (loading) return <div className="empty-panel">正在加载详情...</div>;
  if (error) return <div className="empty-panel error-panel">{error}</div>;
  if (!item) return <div className="empty-panel">未找到商品。</div>;

  return (
    <section className="page-stack">
      <div className="detail-hero">
        <div className="detail-copy">
          <p className="eyebrow">{item.marketplace}</p>
          <h2>{item.title ?? item.legacy_item_id}</h2>
          <p className="muted-note">{item.note ?? "暂无备注。"}</p>
          <div className="detail-meta">
            <div>
              <span>当前价格</span>
              <strong>{formatMoney(item.current_price, item.currency ?? "USD")}</strong>
            </div>
            <div>
              <span>运费</span>
              <strong>{formatMoney(item.current_shipping_cost, item.currency ?? "USD")}</strong>
            </div>
            <div>
              <span>最近抓取</span>
              <strong>{formatUtc(item.last_captured_at)}</strong>
            </div>
          </div>
        </div>
        {item.image_url ? <img className="detail-image" src={item.image_url} alt={item.title ?? "eBay 商品"} /> : null}
      </div>

      <PriceHistoryChart snapshots={item.thirty_day_snapshots} currency={item.currency} />

      <div className="detail-grid">
        <div className="log-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">事件日志</p>
              <h3>最近价格变化</h3>
            </div>
          </div>
          <div className="event-list">
            {item.recent_events.map((event) => (
              <div key={event.id} className="event-row">
                <StatusPill tone={getEventTone(event.event_type)}>
                  {getPriceChangeLabel(event.event_type)}
                </StatusPill>
                <div>
                  <strong>{getCompareWindowLabel(event.compare_window)}</strong>
                  <p>{formatUtc(event.event_time)}</p>
                </div>
                <div>
                  <strong>{formatMoney(event.diff_amount, item.currency ?? "USD")}</strong>
                  <p>{formatPercent(event.diff_rate, true)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="table-shell">
          <div className="section-head">
            <div>
              <p className="eyebrow">历史记录</p>
              <h3>价格快照</h3>
            </div>
            <div className="detail-actions">
              <a className="action-link" href={getItemExportUrl(item.id)}>
                导出 Excel
              </a>
              <a className="action-link" href={item.canonical_item_url ?? item.url} target="_blank" rel="noreferrer">
                打开 eBay
              </a>
            </div>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>抓取时间</th>
                <th>价格</th>
                <th>运费</th>
                <th>总成本</th>
              </tr>
            </thead>
            <tbody>
              {item.thirty_day_snapshots
                .slice()
                .reverse()
                .map((snapshot) => (
                  <tr key={snapshot.id}>
                    <td>{formatUtc(snapshot.capture_time)}</td>
                    <td>{formatMoney(snapshot.price, item.currency ?? "USD")}</td>
                    <td>{formatMoney(snapshot.shipping_cost, item.currency ?? "USD")}</td>
                    <td>{formatMoney(snapshot.total_cost, item.currency ?? "USD")}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
