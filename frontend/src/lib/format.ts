export function formatMoney(value: string | null, currency = "USD") {
  if (value === null) return "--";
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function formatPercent(value: string | null, withSign = false) {
  if (value === null) return "--";
  const numeric = Number(value) * 100;
  const prefix = withSign && numeric > 0 ? "+" : "";
  return `${prefix}${numeric.toFixed(2)}%`;
}

export function formatUtc(value: string | null) {
  if (!value) return "--";
  return new Date(value).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  });
}
