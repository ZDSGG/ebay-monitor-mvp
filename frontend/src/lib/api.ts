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
import { clearStoredAppSecret, getStoredAppSecret } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const appSecret = getStoredAppSecret();
  const initHeaders = new Headers(init?.headers);
  const headers = new Headers();

  headers.set("Content-Type", "application/json");
  if (appSecret) {
    headers.set("X-App-Secret", appSecret);
  }
  initHeaders.forEach((value, key) => {
    headers.set(key, value);
  });

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAppSecret();
    }
    const body = await response.json().catch(() => null);
    const detail = Array.isArray(body?.detail)
      ? body.detail.map((entry: { msg?: string }) => entry?.msg ?? "Request validation failed.").join("; ")
      : typeof body?.detail === "string"
        ? body.detail
        : `Request failed with ${response.status}`;
    throw new Error(detail);
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

export function verifyAppSecret(secret: string) {
  return request<{ authenticated: boolean }>("/auth/verify", {
    method: "POST",
    headers: {
      "X-App-Secret": secret,
    },
    body: JSON.stringify({ secret }),
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
  const appSecret = getStoredAppSecret();
  const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
    method: "DELETE",
    headers: appSecret ? { "X-App-Secret": appSecret } : undefined,
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAppSecret();
    }
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
  const appSecret = getStoredAppSecret();

  const response = await fetch(`${API_BASE_URL}/items/import-csv`, {
    method: "POST",
    headers: appSecret ? { "X-App-Secret": appSecret } : undefined,
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAppSecret();
    }
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<CsvImportResponse>;
}

export async function downloadItemExport(itemId: string) {
  const appSecret = getStoredAppSecret();
  const response = await fetch(`${API_BASE_URL}/reports/items/${itemId}/export`, {
    headers: appSecret ? { "X-App-Secret": appSecret } : undefined,
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAppSecret();
    }
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename\\*?=(?:UTF-8''|\"?)([^\";]+)/i);
  const filename = match?.[1] ? decodeURIComponent(match[1].replace(/"/g, "")) : `item-${itemId}-report.xlsx`;
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
