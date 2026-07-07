import { useState } from "react";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import { ComparisonChart } from "../components/charts/ComparisonChart";
import { useInvestigations } from "../hooks/useInvestigation";
import { useCompare } from "../hooks/useCompare";
import { formatCurrency } from "../lib/utils";

function InvestigationSelect({ label, value, onChange, options }) {
  return (
    <div className="flex-1">
      <label className="text-sm font-medium text-ink">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink focus:border-brand focus:outline-none"
      >
        <option value="">Select an investigation…</option>
        {options.map((inv) => (
          <option key={inv.id} value={inv.id}>
            {inv.company_name || "Untitled investigation"}
          </option>
        ))}
      </select>
    </div>
  );
}

const METRIC_ROWS = [
  ["health_score", "Financial health score"],
  ["risk_score", "Risk score"],
];

export function ComparePage() {
  const [idA, setIdA] = useState("");
  const [idB, setIdB] = useState("");
  const { data: investigations } = useInvestigations();
  const { investigationA, investigationB, isLoading, summary } = useCompare(idA, idB);

  const bothSelected = Boolean(idA && idB);
  // The backend's /compare/ endpoint is currently a literal stub whose
  // response doesn't describe a real comparison -- show an honest
  // empty state instead of that raw debug string.
  const hasSummary = summary?.comparison && summary.comparison !== "not implemented yet";

  const nameOf = (inv) => inv?.company_name || "Untitled investigation";

  const latestFinancial = (inv) => {
    const financials = inv?.financials;
    if (!Array.isArray(financials) || financials.length === 0) return null;
    return [...financials].sort((a, b) => b.year - a.year)[0];
  };

  const chartData =
    investigationA && investigationB
      ? [
          {
            metric: "Health score",
            A: investigationA.health_score ?? 0,
            B: investigationB.health_score ?? 0,
          },
          { metric: "Risk score", A: investigationA.risk_score ?? 0, B: investigationB.risk_score ?? 0 },
        ]
      : [];

  return (
    <PageWrapper>
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">Compare</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">
          Compare two investigations
        </h1>
      </div>

      <Card className="mb-6 flex flex-col gap-4 sm:flex-row">
        <InvestigationSelect label="Company A" value={idA} onChange={setIdA} options={investigations ?? []} />
        <InvestigationSelect label="Company B" value={idB} onChange={setIdB} options={investigations ?? []} />
      </Card>

      {!bothSelected && (
        <Card>
          <EmptyState>Select two investigations above to compare them.</EmptyState>
        </Card>
      )}

      {bothSelected && isLoading && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {bothSelected && !isLoading && investigationA && investigationB && (
        <div className="flex flex-col gap-6">
          <Card title="Metrics">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-line text-xs uppercase tracking-wide text-ink-faint">
                    <th className="py-2 pr-4 font-medium">Metric</th>
                    <th className="py-2 pr-4 font-medium">{nameOf(investigationA)}</th>
                    <th className="py-2 font-medium">{nameOf(investigationB)}</th>
                  </tr>
                </thead>
                <tbody>
                  {METRIC_ROWS.map(([key, label]) => (
                    <tr key={key} className="border-b border-line last:border-0">
                      <td className="py-2 pr-4 text-ink-muted">{label}</td>
                      <td className="data-figure py-2 pr-4 text-ink">{investigationA[key] ?? "—"}</td>
                      <td className="data-figure py-2 text-ink">{investigationB[key] ?? "—"}</td>
                    </tr>
                  ))}
                  <tr className="border-b border-line last:border-0">
                    <td className="py-2 pr-4 text-ink-muted">Latest revenue</td>
                    <td className="data-figure py-2 pr-4 text-ink">
                      {formatCurrency(latestFinancial(investigationA)?.revenue)}
                    </td>
                    <td className="data-figure py-2 text-ink">
                      {formatCurrency(latestFinancial(investigationB)?.revenue)}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 text-ink-muted">Latest profit</td>
                    <td className="data-figure py-2 pr-4 text-ink">
                      {formatCurrency(latestFinancial(investigationA)?.profit)}
                    </td>
                    <td className="data-figure py-2 text-ink">
                      {formatCurrency(latestFinancial(investigationB)?.profit)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Score comparison">
            <ComparisonChart data={chartData} labelA={nameOf(investigationA)} labelB={nameOf(investigationB)} />
          </Card>

          <Card title="AI comparison summary">
            {!hasSummary ? (
              <EmptyState>An AI-generated comparison isn't available for these investigations yet.</EmptyState>
            ) : (
              <p className="whitespace-pre-line text-sm leading-relaxed text-ink">{summary.comparison}</p>
            )}
          </Card>
        </div>
      )}
    </PageWrapper>
  );
}
