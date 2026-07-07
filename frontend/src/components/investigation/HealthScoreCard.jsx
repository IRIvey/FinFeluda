import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { scoreTone } from "../../lib/utils";

const SUBSCORE_LABELS = ["growth", "liquidity", "profitability", "debt", "efficiency"];

export function HealthScoreCard({ healthScore, subscores }) {
  const tone = scoreTone(healthScore);

  return (
    <Card title="Financial health score" tier={tone}>
      <div className="flex items-baseline gap-2">
        <span className="data-figure text-5xl font-semibold" style={{ color: `var(--color-${tone})` }}>
          {healthScore ?? "—"}
        </span>
        <span className="text-sm text-ink-faint">/ 100</span>
      </div>

      <div className="mt-5">
        {subscores ? (
          <ul className="flex flex-col gap-2">
            {SUBSCORE_LABELS.filter((key) => subscores[key] !== undefined).map((key) => (
              <li key={key} className="flex items-center justify-between text-sm">
                <span className="capitalize text-ink-muted">{key}</span>
                <span className="data-figure font-medium text-ink">{subscores[key]}</span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState>
            Growth, liquidity, profitability, debt, and efficiency sub-scores aren't broken out for
            this investigation yet.
          </EmptyState>
        )}
      </div>
    </Card>
  );
}
