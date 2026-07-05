import { TrendChart } from "./TrendChart";

export function ExpenseChart({ data }) {
  return (
    <TrendChart data={data} dataKey="expenses" label="Expenses" color="var(--color-risk-medium)" />
  );
}
