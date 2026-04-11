import { formatMoney, formatPercent } from "../lib/format";
import { getPriceChangeLabel } from "../lib/itemLabels";
import { StatusPill } from "./StatusPill";

type Props = {
  diff: string | null;
  rate: string | null;
  status: string;
  currency: string | null;
};

export function PriceChangeCell({ diff, rate, status, currency }: Props) {
  const tone = status === "PRICE_DROP" ? "drop" : status === "PRICE_RISE" ? "rise" : "neutral";

  return (
    <div className="change-cell">
      <StatusPill tone={tone}>{getPriceChangeLabel(status)}</StatusPill>
      <strong>{formatMoney(diff, currency ?? "USD")}</strong>
      <span>{formatPercent(rate, true)}</span>
    </div>
  );
}
