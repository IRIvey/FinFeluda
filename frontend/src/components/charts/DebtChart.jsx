import { TrendChart } from "./TrendChart";

export function DebtChart({ data }) {
  return <TrendChart data={data} dataKey="debt" label="Debt" color="var(--color-risk-high)" />;
}
