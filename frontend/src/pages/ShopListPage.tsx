import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createShop, deleteShop, getShops, scanShop } from "../lib/api";
import { formatUtc } from "../lib/format";
import { StatusPill } from "../components/StatusPill";
import type { ShopResponse } from "../types";

function getShopStatusTone(status: string) {
  return status === "ACTIVE" ? "rise" : "neutral";
}

function getScanTone(status: string | null | undefined) {
  if (status === "SUCCESS") return "rise";
  if (status === "FAILED") return "drop";
  return "neutral";
}

export function ShopListPage() {
  const [shops, setShops] = useState<ShopResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [formUrl, setFormUrl] = useState("");
  const [formNote, setFormNote] = useState("");
  const [search, setSearch] = useState("");

  async function loadShops() {
    const data = await getShops();
    setShops(data);
  }

  useEffect(() => {
    loadShops()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filteredShops = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) {
      return shops;
    }
    return shops.filter((shop) =>
      [shop.shop_name, shop.seller_username, shop.marketplace, shop.note]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(keyword),
    );
  }, [shops, search]);

  async function handleCreateShop(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const created = await createShop({ url: formUrl, note: formNote || undefined });
      await loadShops();
      setFormUrl("");
      setFormNote("");
      setMessage(`店铺「${created.shop_name}」已录入，并已执行首次扫描。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "店铺录入失败。");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleScanShop(shop: ShopResponse) {
    setScanningId(shop.id);
    setError(null);
    setMessage(null);
    try {
      const result = await scanShop(shop.id);
      await loadShops();
      setMessage(`店铺「${shop.shop_name}」扫描完成，成功 ${result.succeeded}，失败 ${result.failed}。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "店铺扫描失败。");
    } finally {
      setScanningId(null);
    }
  }

  async function handleDeleteShop(shop: ShopResponse) {
    const confirmed = window.confirm(`确认移除店铺监控“${shop.shop_name}”吗？相关店铺数据会一起删除。`);
    if (!confirmed) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await deleteShop(shop.id);
      await loadShops();
      setMessage(`店铺「${shop.shop_name}」已移除监控。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "店铺移除失败。");
    }
  }

  if (loading) {
    return <div className="empty-panel">正在加载店铺工作台...</div>;
  }

  return (
    <section className="workspace-stack">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">店铺监控</p>
          <h2>竞店列表</h2>
          <p className="workspace-copy">录入竞店、触发扫描、查看店铺画像与近日报表。</p>
        </div>
      </div>

      {message ? <div className="notice-banner success-panel">{message}</div> : null}
      {error ? <div className="notice-banner error-panel">{error}</div> : null}

      <div className="page-grid">
        <div className="form-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">录入竞店</p>
              <h3>新增店铺监控</h3>
            </div>
          </div>
          <form className="stack-form" onSubmit={handleCreateShop}>
            <label>
              <span>店铺链接</span>
              <input
                value={formUrl}
                onChange={(event) => setFormUrl(event.target.value)}
                placeholder="https://www.ebay.com/usr/... 或 /str/..."
                required
              />
            </label>
            <label>
              <span>备注</span>
              <textarea
                value={formNote}
                onChange={(event) => setFormNote(event.target.value)}
                rows={5}
                placeholder="可选：记录竞店定位、产品线、地区等"
              />
            </label>
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? "录入中..." : "录入店铺并首次扫描"}
            </button>
          </form>
        </div>

        <div className="table-shell">
          <div className="section-head">
            <div>
              <p className="eyebrow">店铺清单</p>
              <h3>已监控竞店</h3>
            </div>
            <div className="header-actions">
              <input
                className="shop-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="搜索店铺名 / 卖家 / marketplace"
              />
            </div>
          </div>

          <div className="shop-list-grid">
            {filteredShops.map((shop) => (
              <div key={shop.id} className="shop-card">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">{shop.marketplace}</p>
                    <h3>{shop.shop_name}</h3>
                    <p className="muted-note">@{shop.seller_username}</p>
                  </div>
                  <div className="tag-stack">
                    <StatusPill tone={getShopStatusTone(shop.status)}>{shop.status === "ACTIVE" ? "监控中" : "已停用"}</StatusPill>
                    <StatusPill tone={getScanTone(shop.initial_scan?.status)}>{shop.initial_scan?.status ?? "未扫描"}</StatusPill>
                  </div>
                </div>

                <div className="drawer-meta">
                  <span>最近扫描 {formatUtc(shop.last_scanned_at)}</span>
                  <span>创建于 {formatUtc(shop.created_at)}</span>
                </div>

                {shop.note ? <p className="muted-note">{shop.note}</p> : null}

                <div className="row-actions">
                  <Link className="table-action" to={`/shops/${shop.id}`}>
                    查看详情
                  </Link>
                  <button
                    className="table-action"
                    type="button"
                    disabled={scanningId === shop.id}
                    onClick={() => handleScanShop(shop)}
                  >
                    {scanningId === shop.id ? "扫描中..." : "立即扫描"}
                  </button>
                  <a className="table-action" href={shop.shop_url} target="_blank" rel="noreferrer">
                    打开店铺
                  </a>
                  <button className="table-action" type="button" onClick={() => handleDeleteShop(shop)}>
                    移除监控
                  </button>
                </div>
              </div>
            ))}
            {filteredShops.length === 0 ? <div className="empty-inline">暂无店铺数据。</div> : null}
          </div>
        </div>
      </div>
    </section>
  );
}
