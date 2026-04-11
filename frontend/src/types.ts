export type PriceChangeSummary = {
  diff: string | null;
  rate: string | null;
  status: string;
};

export type ItemListEntry = {
  id: string;
  marketplace: string;
  legacy_item_id: string;
  title: string | null;
  url: string;
  note: string | null;
  seller_name: string | null;
  availability: string | null;
  image_url: string | null;
  currency: string | null;
  current_price: string | null;
  current_shipping_cost: string | null;
  total_cost: string | null;
  yesterday_change: PriceChangeSummary;
  weekly_change: PriceChangeSummary;
  is_price_drop: boolean;
  last_captured_at: string | null;
  status: string;
  latest_event_type: string | null;
  latest_event_time: string | null;
  recent_prices: string[];
};

export type ItemListResponse = {
  items: ItemListEntry[];
};

export type CrawlSummary = {
  status: string;
  message: string;
};

export type MonitoredItemResponse = {
  id: string;
  marketplace: string;
  legacy_item_id: string;
  url: string;
  note: string | null;
  status: string;
  title: string | null;
  currency: string | null;
  current_price: string | null;
  current_shipping_cost: string | null;
  seller_name: string | null;
  item_condition: string | null;
  availability: string | null;
  image_url: string | null;
  canonical_item_url: string | null;
  last_captured_at: string | null;
  created_at: string;
  updated_at: string;
  initial_crawl: CrawlSummary;
};

export type ItemCreateResponse = MonitoredItemResponse;

export type ItemSnapshotEntry = {
  id: string;
  price: string;
  shipping_cost: string;
  total_cost: string;
  capture_time: string;
};

export type ItemEventEntry = {
  id: string;
  event_type: string;
  compare_window: string;
  previous_price: string | null;
  current_price: string;
  diff_amount: string | null;
  diff_rate: string | null;
  event_time: string;
};

export type ItemDetailResponse = {
  id: string;
  marketplace: string;
  legacy_item_id: string;
  title: string | null;
  url: string;
  note: string | null;
  status: string;
  currency: string | null;
  current_price: string | null;
  current_shipping_cost: string | null;
  seller_name: string | null;
  item_condition: string | null;
  availability: string | null;
  image_url: string | null;
  canonical_item_url: string | null;
  last_captured_at: string | null;
  thirty_day_snapshots: ItemSnapshotEntry[];
  recent_events: ItemEventEntry[];
};

export type DashboardTrendPoint = {
  capture_date: string;
  average_price: string;
  item_count: number;
};

export type DashboardSummaryResponse = {
  total_items: number;
  today_price_drops: number;
  today_price_rises: number;
  today_delisted: number;
  crawl_success_rate: string;
  average_volatility: string;
  trend_points: DashboardTrendPoint[];
};

export type RecentEventFeedEntry = {
  id: string;
  item_id: string;
  item_title: string | null;
  legacy_item_id: string;
  marketplace: string;
  image_url: string | null;
  event_type: string;
  compare_window: string;
  diff_amount: string | null;
  diff_rate: string | null;
  event_time: string;
};

export type RecentEventListResponse = {
  events: RecentEventFeedEntry[];
};

export type BulkRefreshResult = {
  item_id: string;
  title: string | null;
  status: string;
  message: string;
};

export type BulkRefreshResponse = {
  requested_count: number;
  processed_count: number;
  success_count: number;
  failed_count: number;
  results: BulkRefreshResult[];
};

export type BulkDeactivateResponse = {
  requested_count: number;
  deactivated_count: number;
};

export type BulkDeleteResponse = {
  requested_count: number;
  deleted_count: number;
};

export type CsvImportItemResult = {
  url: string;
  note: string | null;
  status: string;
  item_id: string | null;
  message: string;
};

export type CsvImportResponse = {
  total_rows: number;
  created_count: number;
  skipped_count: number;
  failed_count: number;
  results: CsvImportItemResult[];
};
