import type {
  BulkDeleteResponse,
  BulkDeactivateResponse,
  BulkRefreshResponse,
  CsvImportResponse,
  DashboardSummaryResponse,
  ItemCreateResponse,
  ItemDetailResponse,
  ItemListResponse,
  MonitoredItemResponse,
  RecentEventListResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getItems() {
  return request<ItemListResponse>("/items");
}

export function getItemsDashboardSummary() {
  return request<DashboardSummaryResponse>("/items/dashboard-summary");
}

export function getItemsRecentEvents(limit = 8) {
  return request<RecentEventListResponse>(`/items/recent-events?limit=${limit}`);
}

export function getItemDetail(itemId: string) {
  return request<ItemDetailResponse>(`/items/${itemId}`);
}

export function createItem(payload: { url: string; note?: string }) {
  return request<ItemCreateResponse>("/items", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function refreshItems(itemIds: string[]) {
  return request<BulkRefreshResponse>("/items/bulk-refresh", {
    method: "POST",
    body: JSON.stringify({ item_ids: itemIds }),
  });
}

export function refreshItem(itemId: string) {
  return request<BulkRefreshResponse>(`/items/${itemId}/refresh`, {
    method: "POST",
  });
}

export function deactivateItems(itemIds: string[]) {
  return request<BulkDeactivateResponse>("/items/bulk-deactivate", {
    method: "POST",
    body: JSON.stringify({ item_ids: itemIds }),
  });
}

export function deleteItems(itemIds: string[]) {
  return request<BulkDeleteResponse>("/items/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ item_ids: itemIds }),
  });
}

export async function deleteItem(itemId: string) {
  const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }
}

export function updateItemNote(itemId: string, note: string | null) {
  return request<MonitoredItemResponse>(`/items/${itemId}/note`, {
    method: "PATCH",
    body: JSON.stringify({ note }),
  });
}

export async function importItemsCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/items/import-csv`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<CsvImportResponse>;
}

export function getItemExportUrl(itemId: string) {
  return `${API_BASE_URL}/reports/items/${itemId}/export`;
}
