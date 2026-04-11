import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMoney } from "../lib/format";
import type { DashboardTrendPoint } from "../types";

type Props = {
  points: DashboardTrendPoint[];
  currency: string;
};

export function DashboardTrendChart({ points, currency }: Props) {
  const data = points.map((point) => ({
    label: new Date(point.capture_date).toLocaleDateString("zh-CN", {
      month: "numeric",
      day: "numeric",
      timeZone: "UTC",
    }),
    averagePrice: Number(point.average_price),
    itemCount: point.item_count,
  }));

  return (
    <div className="chart-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">整体波动</p>
          <h3>最近 7 天平均价格走势</h3>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="dashboardArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#53d8fb" stopOpacity="0.38" />
                <stop offset="100%" stopColor="#53d8fb" stopOpacity="0" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
            <XAxis dataKey="label" stroke="#7d8ba3" tickLine={false} axisLine={false} />
            <YAxis stroke="#7d8ba3" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                background: "#0e1825",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                borderRadius: 16,
              }}
              formatter={(value: number, name: string) =>
                name === "averagePrice" ? [formatMoney(String(value), currency), "平均价格"] : [String(value), "商品数"]
              }
            />
            <Area
              type="monotone"
              dataKey="averagePrice"
              stroke="#53d8fb"
              fill="url(#dashboardArea)"
              strokeWidth={2.5}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
