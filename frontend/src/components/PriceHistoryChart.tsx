import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ItemSnapshotEntry } from "../types";

type Props = {
  snapshots: ItemSnapshotEntry[];
  currency: string | null;
};

export function PriceHistoryChart({ snapshots, currency }: Props) {
  const data = snapshots.map((snapshot) => ({
    captureTime: new Date(snapshot.capture_time).toLocaleDateString("zh-CN", {
      month: "numeric",
      day: "numeric",
      timeZone: "UTC",
    }),
    price: Number(snapshot.price),
    totalCost: Number(snapshot.total_cost),
  }));

  return (
    <div className="chart-card">
      <div className="section-head">
        <div>
          <p className="eyebrow">30 天价格曲线</p>
          <h3>价格观测趋势</h3>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(147, 197, 253, 0.08)" vertical={false} />
            <XAxis dataKey="captureTime" stroke="#6b7a90" />
            <YAxis stroke="#6b7a90" />
            <Tooltip
              contentStyle={{
                background: "#0f1723",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                borderRadius: 16,
              }}
              formatter={(value: number) => [
                new Intl.NumberFormat("zh-CN", {
                  style: "currency",
                  currency: currency ?? "USD",
                }).format(value),
              ]}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#51e5c2"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 5, fill: "#b6fff0" }}
            />
            <Line
              type="monotone"
              dataKey="totalCost"
              stroke="#7dd3fc"
              strokeWidth={2}
              strokeDasharray="6 6"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
