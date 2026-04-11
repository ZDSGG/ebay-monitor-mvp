import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { DashboardTrendChart } from "../components/DashboardTrendChart";
import { PriceChangeCell } from "../components/PriceChangeCell";
import { Sparkline } from "../components/Sparkline";
import { StatusPill } from "../components/StatusPill";
import {
  deleteItem,
  deleteItems,
  deactivateItems,
  getItems,
  getItemsDashboardSummary,
  getItemsRecentEvents,
  refreshItem,
  refreshItems,
  updateItemNote,
} from "../lib/api";
import { formatMoney, formatPercent, formatUtc } from "../lib/format";
import {
  getAvailabilityLabel,
  getCompareWindowLabel,
  getEventTone,
  getItemStatusLabel,
  getPriceChangeLabel,
} from "../lib/itemLabels";
import type { BulkRefreshResult, DashboardSummaryResponse, ItemListEntry, RecentEventFeedEntry } from "../types";

const defaultSummary: DashboardSummaryResponse = {
  total_items: 0,
  today_price_drops: 0,
  today_price_rises: 0,
  today_delisted: 0,
  crawl_success_rate: "0.00",
  average_volatility: "0.0000",
  trend_points: [],
};

const PAGE_SIZE = 8;
const POLL_INTERVAL_MS = 60_000;

type SortKey = "captured" | "price" | "total" | "daily" | "weekly" | "title";
type SortDirection = "asc" | "desc";

type OperationDrawerState =
  | { mode: "note"; item: ItemListEntry }
  | {
      mode: "results";
      title: string;
      summary: string;
      results: Array<{ label: string; status: string; detail: string }>;
    };

function readFilter(params: URLSearchParams, key: string, fallback: string) {
  return params.get(key) || fallback;
}

function toNumber(value: string | null | undefined) {
  return value === null || value === undefined ? Number.NEGATIVE_INFINITY : Number(value);
}

function compareStrings(left: string, right: string) {
  return left.localeCompare(right, "zh-CN");
}

export function ItemListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<ItemListEntry[]>([]);
  const [summary, setSummary] = useState<DashboardSummaryResponse>(defaultSummary);
  const [recentEvents, setRecentEvents] = useState<RecentEventFeedEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [search, setSearch] = useState(() => readFilter(searchParams, "q", ""));
  const [marketplace, setMarketplace] = useState(() => readFilter(searchParams, "marketplace", "ALL"));
  const [status, setStatus] = useState(() => readFilter(searchParams, "status", "ALL"));
  const [dropFilter, setDropFilter] = useState(() => readFilter(searchParams, "drop", "ALL"));
  const [updatedWithin, setUpdatedWithin] = useState(() => readFilter(searchParams, "updated", "ALL"));
  const [sortKey, setSortKey] = useState<SortKey>(() => (readFilter(searchParams, "sort", "captured") as SortKey));
  const [sortDirection, setSortDirection] = useState<SortDirection>(() => (readFilter(searchParams, "direction", "desc") as SortDirection));
  const [page, setPage] = useState(() => Number(readFilter(searchParams, "page", "1")));
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [drawerState, setDrawerState] = useState<OperationDrawerState | null>(null);
  const [noteDraft, setNoteDraft] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [lastRefreshAt, setLastRefreshAt] = useState<string | null>(null);
  const [refreshingPanel, setRefreshingPanel] = useState(false);

  async function loadWorkspace(options?: { silent?: boolean }) {
    if (!options?.silent) setRefreshingPanel(true);
    const [itemsResponse, summaryResponse, eventsResponse] = await Promise.all([
      getItems(),
      getItemsDashboardSummary(),
      getItemsRecentEvents(8),
    ]);
    setItems(itemsResponse.items);
    setSummary(summaryResponse);
    setRecentEvents(eventsResponse.events);
    setLastRefreshAt(new Date().toISOString());
    setRefreshingPanel(false);
  }

  useEffect(() => {
    loadWorkspace()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      loadWorkspace({ silent: true }).catch(() => {
        // Keep current view stable if background polling fails.
      });
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (marketplace !== "ALL") params.set("marketplace", marketplace);
    if (status !== "ALL") params.set("status", status);
    if (dropFilter !== "ALL") params.set("drop", dropFilter);
    if (updatedWithin !== "ALL") params.set("updated", updatedWithin);
    if (sortKey !== "captured") params.set("sort", sortKey);
    if (sortDirection !== "desc") params.set("direction", sortDirection);
    if (page > 1) params.set("page", String(page));
    setSearchParams(params, { replace: true });
  }, [search, marketplace, status, dropFilter, updatedWithin, sortKey, sortDirection, page, setSearchParams]);

  const now = Date.now();
  const filteredItems = useMemo(
    () =>
      items.filter((item) => {
        const keyword = search.trim().toLowerCase();
        const haystack = [item.title, item.seller_name, item.legacy_item_id, item.note, item.marketplace]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        if (keyword && !haystack.includes(keyword)) return false;
        if (marketplace !== "ALL" && item.marketplace !== marketplace) return false;
        if (status !== "ALL" && item.status !== status) return false;
        if (dropFilter === "DROP_ONLY" && !item.is_price_drop) return false;
        if (dropFilter === "NON_DROP" && item.is_price_drop) return false;
        if (updatedWithin !== "ALL") {
          if (!item.last_captured_at) return false;
          const diffHours = (now - new Date(item.last_captured_at).getTime()) / 36e5;
          if (updatedWithin === "24H" && diffHours > 24) return false;
          if (updatedWithin === "72H" && diffHours > 72) return false;
          if (updatedWithin === "7D" && diffHours > 24 * 7) return false;
          if (updatedWithin === "STALE" && diffHours <= 24 * 7) return false;
        }
        return true;
      }),
    [items, search, marketplace, status, dropFilter, updatedWithin, now],
  );

  const sortedItems = useMemo(() => {
    const next = [...filteredItems];
    next.sort((left, right) => {
      let value = 0;
      switch (sortKey) {
        case "title":
          value = compareStrings(left.title ?? left.legacy_item_id, right.title ?? right.legacy_item_id);
          break;
        case "price":
          value = toNumber(left.current_price) - toNumber(right.current_price);
          break;
        case "total":
          value = toNumber(left.total_cost) - toNumber(right.total_cost);
          break;
        case "daily":
          value = toNumber(left.yesterday_change.diff) - toNumber(right.yesterday_change.diff);
          break;
        case "weekly":
          value = toNumber(left.weekly_change.diff) - toNumber(right.weekly_change.diff);
          break;
        case "captured":
        default:
          value = new Date(left.last_captured_at ?? 0).getTime() - new Date(right.last_captured_at ?? 0).getTime();
      }
      return sortDirection === "asc" ? value : -value;
    });
    return next;
  }, [filteredItems, sortKey, sortDirection]);

  const totalPages = Math.max(1, Math.ceil(sortedItems.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pagedItems = useMemo(() => sortedItems.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE), [sortedItems, safePage]);

  useEffect(() => {
    if (page !== safePage) setPage(safePage);
  }, [page, safePage]);

  useEffect(() => {
    setPage(1);
  }, [search, marketplace, status, dropFilter, updatedWithin, sortKey, sortDirection]);

  const selectedItems = sortedItems.filter((item) => selectedIds.includes(item.id));
  const marketOptions = Array.from(new Set(items.map((item) => item.marketplace))).sort();
  const allVisibleSelected = pagedItems.length > 0 && pagedItems.every((item) => selectedIds.includes(item.id));
  const currency = sortedItems[0]?.currency ?? items[0]?.currency ?? "USD";

  function showResultsDrawer(title: string, summaryText: string, results: Array<{ label: string; status: string; detail: string }>) {
    setDrawerState({ mode: "results", title, summary: summaryText, results });
  }

  async function reloadWithMessage(message: string) {
    await loadWorkspace();
    setActionMessage(message);
  }

  async function handleManualRefresh() {
    setError(null);
    try {
      await loadWorkspace();
      setActionMessage("工作台数据已刷新。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "工作台刷新失败。");
      setRefreshingPanel(false);
    }
  }

  function resetFilters() {
    setSearch("");
    setMarketplace("ALL");
    setStatus("ALL");
    setDropFilter("ALL");
    setUpdatedWithin("ALL");
    setSortKey("captured");
    setSortDirection("desc");
    setPage(1);
  }

  function toggleSelectAll() {
    if (allVisibleSelected) {
      setSelectedIds((current) => current.filter((itemId) => !pagedItems.some((item) => item.id === itemId)));
      return;
    }
    setSelectedIds((current) => Array.from(new Set([...current, ...pagedItems.map((item) => item.id)])));
  }

  function toggleSelectOne(itemId: string) {
    setSelectedIds((current) => (current.includes(itemId) ? current.filter((value) => value !== itemId) : [...current, itemId]));
  }

  function handleSort(nextKey: SortKey) {
    if (sortKey === nextKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(nextKey);
    setSortDirection(nextKey === "title" ? "asc" : "desc");
  }

  function renderSortLabel(label: string, key: SortKey) {
    if (sortKey !== key) return label;
    return `${label} ${sortDirection === "asc" ? "↑" : "↓"}`;
  }

  function exportRows(rows: ItemListEntry[]) {
    const csvRows = [
      [
        "标题",
        "卖家",
        "Item ID",
        "Marketplace",
        "当前价格",
        "运费",
        "总价",
        "昨日变化",
        "周变化",
        "状态",
        "最近事件",
        "抓取时间",
      ],
      ...rows.map((item) => [
        item.title ?? item.legacy_item_id,
        item.seller_name ?? "",
        item.legacy_item_id,
        item.marketplace,
        item.current_price ?? "",
        item.current_shipping_cost ?? "",
        item.total_cost ?? "",
        item.yesterday_change.diff ?? "",
        item.weekly_change.diff ?? "",
        item.status,
        item.latest_event_type ?? "",
        item.last_captured_at ?? "",
      ]),
    ];

    const content = csvRows
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, "\"\"")}"`).join(","))
      .join("\n");
    const blob = new Blob(["\uFEFF", content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `ebay-monitor-items-${new Date().toISOString().slice(0, 10)}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    setActionMessage(`已导出 ${rows.length} 条记录。`);
    showResultsDrawer(
      "导出结果",
      `本次已导出 ${rows.length} 条商品记录。`,
      rows.map((item) => ({
        label: item.title ?? item.legacy_item_id,
        status: "EXPORTED",
        detail: `${item.marketplace} · ${formatMoney(item.current_price, item.currency ?? "USD")}`,
      })),
    );
  }

  async function handleBatchRefresh() {
    if (selectedIds.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const result = await refreshItems(selectedIds);
      await reloadWithMessage(`批量刷新完成，成功 ${result.success_count} 条，失败 ${result.failed_count} 条。`);
      showResultsDrawer(
        "批量刷新结果",
        `共请求 ${result.requested_count} 条，实际处理 ${result.processed_count} 条。`,
        result.results.map((entry: BulkRefreshResult) => ({
          label: entry.title ?? entry.item_id,
          status: entry.status,
          detail: entry.message,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量刷新失败。");
    } finally {
      setBusy(false);
    }
  }

  async function handleBatchDeactivate() {
    if (selectedIds.length === 0) return;
    const confirmed = window.confirm(`确认停用选中的 ${selectedIds.length} 个商品吗？`);
    if (!confirmed) return;

    setBusy(true);
    setError(null);
    try {
      const selected = items.filter((item) => selectedIds.includes(item.id));
      const result = await deactivateItems(selectedIds);
      setSelectedIds([]);
      await reloadWithMessage(`已停用 ${result.deactivated_count} 个商品。`);
      showResultsDrawer(
        "批量停用结果",
        `共请求 ${result.requested_count} 条，成功停用 ${result.deactivated_count} 条。`,
        selected.map((item) => ({
          label: item.title ?? item.legacy_item_id,
          status: "INACTIVE",
          detail: `${item.marketplace} · 已停用`,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量停用失败。");
    } finally {
      setBusy(false);
    }
  }

  async function handleBatchDelete() {
    if (selectedIds.length === 0) return;
    const confirmed = window.confirm(`确认从监控池中彻底移除选中的 ${selectedIds.length} 个商品吗？此操作会删除历史快照和事件记录。`);
    if (!confirmed) return;

    setBusy(true);
    setError(null);
    try {
      const selected = items.filter((item) => selectedIds.includes(item.id));
      const result = await deleteItems(selectedIds);
      setSelectedIds([]);
      await reloadWithMessage(`已从监控池移除 ${result.deleted_count} 个商品。`);
      showResultsDrawer(
        "批量移除结果",
        `共请求 ${result.requested_count} 条，成功移除 ${result.deleted_count} 条。`,
        selected.map((item) => ({
          label: item.title ?? item.legacy_item_id,
          status: "DELETED",
          detail: `${item.marketplace} · 已从监控池移除`,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量移除失败。");
    } finally {
      setBusy(false);
    }
  }

  async function handleRowRefresh(itemId: string) {
    setBusy(true);
    setError(null);
    try {
      const result = await refreshItem(itemId);
      const rowResult = result.results[0];
      await reloadWithMessage(rowResult?.message ?? "刷新完成。");
      if (rowResult) {
        showResultsDrawer("单条刷新结果", rowResult.message, [
          {
            label: rowResult.title ?? rowResult.item_id,
            status: rowResult.status,
            detail: rowResult.message,
          },
        ]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "刷新失败。");
    } finally {
      setBusy(false);
    }
  }

  async function handleRowDelete(item: ItemListEntry) {
    const confirmed = window.confirm(`确认从监控池移除「${item.title ?? item.legacy_item_id}」吗？此操作会删除历史快照和事件记录。`);
    if (!confirmed) return;

    setBusy(true);
    setError(null);
    try {
      await deleteItem(item.id);
      setSelectedIds((current) => current.filter((value) => value !== item.id));
      await reloadWithMessage("商品已从监控池移除。");
      showResultsDrawer("移除结果", "商品已成功从监控池移除。", [
        {
          label: item.title ?? item.legacy_item_id,
          status: "DELETED",
          detail: `${item.marketplace} · 已移除`,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "移除失败。");
    } finally {
      setBusy(false);
    }
  }

  function openNoteDrawer(item: ItemListEntry) {
    setNoteDraft(item.note ?? "");
    setDrawerState({ mode: "note", item });
  }

  async function handleSaveNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!drawerState || drawerState.mode !== "note") return;

    setSavingNote(true);
    setError(null);
    try {
      await updateItemNote(drawerState.item.id, noteDraft.trim() || null);
      await reloadWithMessage("备注已更新。");
      showResultsDrawer("备注更新结果", "商品备注已成功更新。", [
        {
          label: drawerState.item.title ?? drawerState.item.legacy_item_id,
          status: "UPDATED",
          detail: noteDraft.trim() || "备注已清空",
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "备注更新失败。");
    } finally {
      setSavingNote(false);
    }
  }

  if (loading) return <div className="empty-panel">正在加载监控工作台...</div>;

  return (
    <section className="workspace-stack">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">监控工作台</p>
          <h2>eBay 商品监控中心</h2>
          <p className="workspace-copy">集中查看价格变化、异常事件和抓取状态，并支持批量处理。</p>
        </div>
        <div className="header-actions">
          <Link className="action-link" to="/items/new">
            新增商品
          </Link>
          <Link className="action-link" to="/items/new">
            批量导入
          </Link>
          <button className="ghost-button" type="button" onClick={() => exportRows(selectedItems.length > 0 ? selectedItems : sortedItems)}>
            导出数据
          </button>
        </div>
      </div>

      {actionMessage ? <div className="notice-banner success-panel">{actionMessage}</div> : null}
      {error ? <div className="notice-banner error-panel">{error}</div> : null}

      <div className="stats-grid">
        <div className="stat-card">
          <span>总商品数</span>
          <strong>{summary.total_items}</strong>
          <p>当前在监控池中的商品数量</p>
        </div>
        <div className="stat-card">
          <span>今日降价</span>
          <strong>{summary.today_price_drops}</strong>
          <p>以 1 日对比事件统计</p>
        </div>
        <div className="stat-card">
          <span>今日涨价</span>
          <strong>{summary.today_price_rises}</strong>
          <p>今日捕获到的上涨商品数</p>
        </div>
        <div className="stat-card">
          <span>今日下架</span>
          <strong>{summary.today_delisted}</strong>
          <p>最近一次抓取显示不可售</p>
        </div>
        <div className="stat-card">
          <span>抓取成功率</span>
          <strong>{summary.crawl_success_rate}%</strong>
          <p>按今日抓取任务计算</p>
        </div>
        <div className="stat-card">
          <span>平均波动</span>
          <strong>{formatPercent(summary.average_volatility, true)}</strong>
          <p>按日级变化绝对值平均</p>
        </div>
      </div>

      <div className="dashboard-grid">
        <DashboardTrendChart points={summary.trend_points} currency={currency} />

        <div className="event-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">异常事件</p>
              <h3>最近价格异常</h3>
            </div>
            <div className="panel-meta">
              <span>{refreshingPanel ? "刷新中..." : "自动轮询 60 秒"}</span>
              <span>上次刷新 {formatUtc(lastRefreshAt)}</span>
              <button className="ghost-button" type="button" onClick={handleManualRefresh} disabled={refreshingPanel}>
                立即刷新工作台
              </button>
            </div>
          </div>
          <div className="anomaly-list">
            {recentEvents.map((event) => (
              <Link key={event.id} className="anomaly-row" to={`/items/${event.item_id}`}>
                <div className="anomaly-row-main">
                  <StatusPill tone={getEventTone(event.event_type)}>{getPriceChangeLabel(event.event_type)}</StatusPill>
                  <div>
                    <strong>{event.item_title ?? event.legacy_item_id}</strong>
                    <p>
                      {event.marketplace} · {getCompareWindowLabel(event.compare_window)}
                    </p>
                  </div>
                </div>
                <div className="anomaly-row-meta">
                  <strong>{formatMoney(event.diff_amount, currency)}</strong>
                  <p>{formatPercent(event.diff_rate, true)}</p>
                  <span>{formatUtc(event.event_time)}</span>
                </div>
              </Link>
            ))}
            {recentEvents.length === 0 ? <div className="empty-inline">最近没有异常事件。</div> : null}
          </div>
        </div>
      </div>

      <div className="filter-panel">
        <div className="filter-row">
          <label className="filter-field filter-field-wide">
            <span>搜索</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="标题 / 卖家 / Item ID / 备注" />
          </label>
          <label className="filter-field">
            <span>Marketplace</span>
            <select value={marketplace} onChange={(event) => setMarketplace(event.target.value)}>
              <option value="ALL">全部</option>
              {marketOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span>状态</span>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="ALL">全部</option>
              <option value="ACTIVE">监控中</option>
              <option value="INACTIVE">已停用</option>
            </select>
          </label>
          <label className="filter-field">
            <span>是否降价</span>
            <select value={dropFilter} onChange={(event) => setDropFilter(event.target.value)}>
              <option value="ALL">全部</option>
              <option value="DROP_ONLY">仅降价</option>
              <option value="NON_DROP">未降价</option>
            </select>
          </label>
          <label className="filter-field">
            <span>更新时间</span>
            <select value={updatedWithin} onChange={(event) => setUpdatedWithin(event.target.value)}>
              <option value="ALL">全部</option>
              <option value="24H">24 小时内</option>
              <option value="72H">3 天内</option>
              <option value="7D">7 天内</option>
              <option value="STALE">7 天未更新</option>
            </select>
          </label>
        </div>
        <div className="filter-actions">
          <span>当前筛选结果 {sortedItems.length} 条，链接地址会自动保留筛选条件。</span>
          <div className="header-actions">
            <button className="ghost-button" type="button" onClick={() => handleSort("captured")}>
              {renderSortLabel("按抓取时间", "captured")}
            </button>
            <button className="ghost-button" type="button" onClick={() => handleSort("price")}>
              {renderSortLabel("按当前价格", "price")}
            </button>
            <button className="ghost-button" type="button" onClick={resetFilters}>
              重置筛选
            </button>
          </div>
        </div>
      </div>

      <div className="table-panel">
        <div className="table-toolbar">
          <div>
            <p className="eyebrow">商品表格</p>
            <h3>监控清单</h3>
          </div>
          <div className="toolbar-metrics">
            <span>当前结果 {sortedItems.length} 条</span>
            <span>当前页 {safePage}/{totalPages}</span>
            <span>已选择 {selectedIds.length} 条</span>
          </div>
        </div>

        {selectedIds.length > 0 ? (
          <div className="bulk-bar">
            <span>已选择 {selectedIds.length} 个商品</span>
            <div className="bulk-actions">
              <button className="ghost-button" type="button" disabled={busy} onClick={handleBatchRefresh}>
                批量刷新
              </button>
              <button className="ghost-button" type="button" onClick={() => exportRows(selectedItems.length > 0 ? selectedItems : sortedItems)}>
                批量导出
              </button>
              <button className="ghost-button danger-button" type="button" disabled={busy} onClick={handleBatchDeactivate}>
                批量停用
              </button>
              <button className="ghost-button danger-button" type="button" disabled={busy} onClick={handleBatchDelete}>
                批量移除
              </button>
            </div>
          </div>
        ) : null}

        <div className="table-scroll">
          <table className="data-table workspace-table">
            <thead>
              <tr>
                <th>
                  <input type="checkbox" checked={allVisibleSelected} onChange={toggleSelectAll} aria-label="全选当前页" />
                </th>
                <th>图片</th>
                <th>
                  <button className="sort-button" type="button" onClick={() => handleSort("title")}>
                    {renderSortLabel("商品标题", "title")}
                  </button>
                </th>
                <th>Marketplace</th>
                <th>
                  <button className="sort-button" type="button" onClick={() => handleSort("price")}>
                    {renderSortLabel("当前价格", "price")}
                  </button>
                </th>
                <th>运费</th>
                <th>
                  <button className="sort-button" type="button" onClick={() => handleSort("total")}>
                    {renderSortLabel("总价", "total")}
                  </button>
                </th>
                <th>
                  <button className="sort-button" type="button" onClick={() => handleSort("daily")}>
                    {renderSortLabel("日变化", "daily")}
                  </button>
                </th>
                <th>
                  <button className="sort-button" type="button" onClick={() => handleSort("weekly")}>
                    {renderSortLabel("周变化", "weekly")}
                  </button>
                </th>
                <th>最近 7 天趋势</th>
                <th>状态</th>
                <th>事件</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {pagedItems.map((item) => (
                <tr key={item.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={() => toggleSelectOne(item.id)}
                      aria-label={`选择 ${item.title ?? item.legacy_item_id}`}
                    />
                  </td>
                  <td>
                    <div className="thumb-shell">
                      {item.image_url ? <img className="item-thumb" src={item.image_url} alt={item.title ?? item.legacy_item_id} /> : <span>无图</span>}
                    </div>
                  </td>
                  <td>
                    <div className="item-main">
                      <Link className="item-link" to={`/items/${item.id}`}>
                        {item.title ?? item.legacy_item_id}
                      </Link>
                      <p className="muted-row">
                        {item.seller_name ?? "未知卖家"} · ID {item.legacy_item_id}
                      </p>
                      {item.note ? <p className="muted-row">{item.note}</p> : null}
                    </div>
                  </td>
                  <td>
                    <div className="stacked-meta">
                      <strong>{item.marketplace}</strong>
                      <span>{getAvailabilityLabel(item.availability)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="price-stack">
                      <strong>{formatMoney(item.current_price, item.currency ?? "USD")}</strong>
                      <span>{formatUtc(item.last_captured_at)}</span>
                    </div>
                  </td>
                  <td>{formatMoney(item.current_shipping_cost, item.currency ?? "USD")}</td>
                  <td>{formatMoney(item.total_cost, item.currency ?? "USD")}</td>
                  <td>
                    <PriceChangeCell
                      diff={item.yesterday_change.diff}
                      rate={item.yesterday_change.rate}
                      status={item.yesterday_change.status}
                      currency={item.currency}
                    />
                  </td>
                  <td>
                    <PriceChangeCell
                      diff={item.weekly_change.diff}
                      rate={item.weekly_change.rate}
                      status={item.weekly_change.status}
                      currency={item.currency}
                    />
                  </td>
                  <td>
                    <Sparkline
                      values={item.recent_prices}
                      tone={item.is_price_drop ? "drop" : item.weekly_change.status === "PRICE_RISE" ? "rise" : "neutral"}
                    />
                  </td>
                  <td>
                    <div className="tag-stack">
                      <StatusPill tone={item.status === "ACTIVE" ? "rise" : "neutral"}>
                        {getItemStatusLabel(item.status)}
                      </StatusPill>
                      <span className="sub-tag">{getAvailabilityLabel(item.availability)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="tag-stack">
                      <StatusPill tone={getEventTone(item.latest_event_type)}>
                        {item.latest_event_type ? getPriceChangeLabel(item.latest_event_type) : "暂无事件"}
                      </StatusPill>
                      <span className="sub-tag">{item.latest_event_type ? formatUtc(item.latest_event_time) : "--"}</span>
                    </div>
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="table-action" type="button" disabled={busy} onClick={() => handleRowRefresh(item.id)}>
                        立即刷新
                      </button>
                      <Link className="table-action" to={`/items/${item.id}`}>
                        查看详情
                      </Link>
                      <button className="table-action" type="button" disabled={busy} onClick={() => openNoteDrawer(item)}>
                        编辑备注
                      </button>
                      <button className="table-action danger-button" type="button" disabled={busy} onClick={() => handleRowDelete(item)}>
                        移除监控
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {pagedItems.length === 0 ? <div className="empty-inline">没有符合筛选条件的商品。</div> : null}
        </div>

        <div className="pagination-bar">
          <span>
            显示 {sortedItems.length === 0 ? 0 : (safePage - 1) * PAGE_SIZE + 1} - {Math.min(safePage * PAGE_SIZE, sortedItems.length)} / {sortedItems.length}
          </span>
          <div className="bulk-actions">
            <button className="ghost-button" type="button" disabled={safePage <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
              上一页
            </button>
            <button className="ghost-button" type="button" disabled={safePage >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>
              下一页
            </button>
          </div>
        </div>
      </div>

      {drawerState ? (
        <div className="drawer-backdrop" onClick={() => setDrawerState(null)}>
          <aside className="side-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-head">
              <div>
                <p className="eyebrow">{drawerState.mode === "note" ? "备注编辑" : "操作结果"}</p>
                <h3>{drawerState.mode === "note" ? drawerState.item.title ?? drawerState.item.legacy_item_id : drawerState.title}</h3>
              </div>
              <button className="ghost-button" type="button" onClick={() => setDrawerState(null)}>
                关闭
              </button>
            </div>

            {drawerState.mode === "note" ? (
              <form className="drawer-form" onSubmit={handleSaveNote}>
                <div className="drawer-meta">
                  <span>{drawerState.item.marketplace}</span>
                  <span>ID {drawerState.item.legacy_item_id}</span>
                </div>
                <label className="filter-field">
                  <span>备注内容</span>
                  <textarea
                    value={noteDraft}
                    onChange={(event) => setNoteDraft(event.target.value)}
                    rows={8}
                    placeholder="输入商品备注"
                  />
                </label>
                <div className="drawer-actions">
                  <button className="primary-button" type="submit" disabled={savingNote}>
                    {savingNote ? "保存中..." : "保存备注"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="result-panel">
                <p className="drawer-summary">{drawerState.summary}</p>
                <div className="result-list">
                  {drawerState.results.map((result, index) => (
                    <div key={`${result.label}-${index}`} className="result-row">
                      <div>
                        <strong>{result.label}</strong>
                        <p>{result.detail}</p>
                      </div>
                      <StatusPill tone={getEventTone(result.status)}>
                        {result.status === "SUCCESS"
                          ? "成功"
                          : result.status === "FAILED"
                            ? "失败"
                            : result.status === "INACTIVE"
                              ? "已停用"
                              : result.status === "DELETED"
                                ? "已移除"
                              : result.status === "UPDATED"
                                ? "已更新"
                                : result.status === "EXPORTED"
                                  ? "已导出"
                                  : result.status}
                      </StatusPill>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </aside>
        </div>
      ) : null}
    </section>
  );
}
