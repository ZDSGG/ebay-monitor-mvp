export function getPriceChangeLabel(status: string) {
  switch (status) {
    case "NO_DATA":
      return "暂无数据";
    case "NO_CHANGE":
      return "无变化";
    case "PRICE_DROP":
      return "降价";
    case "PRICE_RISE":
      return "涨价";
    default:
      return status;
  }
}

export function getCompareWindowLabel(value: string) {
  switch (value) {
    case "1d":
      return "昨日对比";
    case "7d":
      return "近 7 天";
    default:
      return value;
  }
}

export function getItemStatusLabel(status: string) {
  switch (status) {
    case "ACTIVE":
      return "监控中";
    case "INACTIVE":
      return "已停用";
    default:
      return status;
  }
}

export function getAvailabilityLabel(value: string | null) {
  if (!value) return "未知";

  const normalized = value.toLowerCase();
  if (normalized.includes("in stock") || normalized.includes("available")) return "在售";
  if (normalized.includes("out of stock")) return "缺货";
  if (normalized.includes("sold")) return "已售出";
  if (normalized.includes("unavailable")) return "不可用";
  return value;
}

export function getEventTone(eventType: string | null) {
  if (eventType === "PRICE_DROP") return "drop";
  if (eventType === "PRICE_RISE") return "rise";
  return "neutral";
}
