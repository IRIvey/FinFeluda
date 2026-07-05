import { TrendChart } from "./TrendChart";

export function CashFlowChart({ data }) {
  return (
    <TrendChart data={data} dataKey="cash_flow" label="Cash flow" color="var(--color-tier-2)" />
  );
}
