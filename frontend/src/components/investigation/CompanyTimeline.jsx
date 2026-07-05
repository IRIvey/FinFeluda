import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { formatCurrency } from "../../lib/utils";

/**
 * The backend has a timeline prompt builder (app/prompts/timeline.py)
 * but no endpoint wires it up yet, so there's no real "event" data to
 * show. Until then, this renders an honest financial-year timeline
 * from whatever yearly figures exist instead of inventing milestones.
 */
export function CompanyTimeline({ financials }) {
  const hasData = Array.isArray(financials) && financials.length > 0;
  const sorted = hasData ? [...financials].sort((a, b) => a.year - b.year) : [];

  return (
    <Card title="Timeline">
      {!hasData ? (
        <EmptyState>No dated financial history is available for this investigation yet.</EmptyState>
      ) : (
        <ol className="flex flex-col gap-0">
          {sorted.map((row, index) => (
            <li key={row.year} className="relative flex gap-4 pb-6 last:pb-0">
              <div className="flex flex-col items-center">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-brand" />
                {index < sorted.length - 1 && (
                  <span className="mt-1 w-px flex-1 bg-line-strong" aria-hidden="true" />
                )}
              </div>
              <div className="-mt-1">
                <p className="data-figure text-sm font-semibold text-ink">{row.year}</p>
                <p className="mt-0.5 text-sm text-ink-muted">
                  Revenue {formatCurrency(row.revenue, row.currency)} · Profit{" "}
                  {formatCurrency(row.profit, row.currency)}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}
