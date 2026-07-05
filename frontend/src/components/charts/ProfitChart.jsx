import { TrendChart } from "./TrendChart";

export function ProfitChart({ data }) {
  return <TrendChart data={data} dataKey="profit" label="Profit" color="var(--color-brand)" />;
}
