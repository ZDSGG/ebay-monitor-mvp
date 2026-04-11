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

export type ShopScanSummary = {
  status: string;
  message: string;
};

export type ShopResponse = {
  id: string;
  marketplace: string;
  seller_username: string;
  shop_name: string;
  shop_url: string;
  note: string | null;
  status: string;
  scan_enabled: boolean;
  last_scanned_at: string | null;
  created_at: string;
  updated_at: string;
  initial_scan: ShopScanSummary | null;
};

export type ShopDailyStatEntry = {
  id: string;
  stat_date: string;
  active_listing_count: number;
  new_listing_count: number;
  ended_listing_count: number;
  price_drop_count: number;
  price_rise_count: number;
  average_price: string | null;
  scanned_at: string;
};

export type ShopListingEntry = {
  id: string;
  legacy_item_id: string;
  title: string;
  item_url: string;
  image_url: string | null;
  currency: string | null;
  current_price: string | null;
  current_shipping_cost: string | null;
  total_cost: string | null;
  availability: string | null;
  sales_summary: string | null;
  listing_status: string;
  first_seen_at: string;
  last_seen_at: string;
  last_price_change_at: string | null;
};

export type ShopPortrait = {
  active_listing_count: number;
  active_ratio: string;
  average_price: string | null;
  last_7d_new_count: number;
  last_7d_ended_count: number;
  last_7d_price_drop_count: number;
  open_alert_count: number;
};

export type ShopDetailResponse = {
  id: string;
  marketplace: string;
  seller_username: string;
  shop_name: string;
  shop_url: string;
  note: string | null;
  status: string;
  scan_enabled: boolean;
  last_scanned_at: string | null;
  created_at: string;
  updated_at: string;
  portrait: ShopPortrait;
  recent_stats: ShopDailyStatEntry[];
  active_listings: ShopListingEntry[];
};

export type ShopCreateResponse = ShopResponse;

export type ShopScanTriggerResponse = {
  requested: number;
  succeeded: number;
  failed: number;
  trigger_source: string;
};

export type AlertEntry = {
  id: string;
  shop_id: string | null;
  shop_name: string | null;
  seller_username: string | null;
  alert_rule_id: string | null;
  alert_type: string;
  severity: string;
  status: string;
  title: string;
  message: string;
  triggered_at: string;
  resolved_at: string | null;
  payload_json: Record<string, unknown> | null;
};

export type AlertListResponse = {
  alerts: AlertEntry[];
};

export type AlertResolveResponse = {
  id: string;
  status: string;
  resolved_at: string | null;
};

export type AlertRuleEntry = {
  id: string;
  shop_id: string | null;
  shop_name: string | null;
  rule_name: string;
  rule_type: string;
  threshold_value: string | null;
  threshold_unit: string | null;
  is_enabled: boolean;
  description: string | null;
  params_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type AlertRuleListResponse = {
  rules: AlertRuleEntry[];
};
