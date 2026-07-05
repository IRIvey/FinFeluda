import { TrendChart } from "./TrendChart";

export function RevenueChart({ data }) {
  return <TrendChart data={data} dataKey="revenue" label="Revenue" color="var(--color-tier-1)" />;
}
