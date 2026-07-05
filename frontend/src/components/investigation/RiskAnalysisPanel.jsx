import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { Progress } from "../ui/Progress";
import { scoreTone } from "../../lib/utils";

const SUB_SCORES = [
  ["financial_risk_score", "Financial risk"],
  ["operational_risk_score", "Operational risk"],
  ["business_risk_score", "Business risk"],
];

export function RiskAnalysisPanel({ riskScore, riskAnalysis }) {
  const tone = scoreTone(100 - (riskScore ?? 50));

  return (
    <Card title="Risk analysis" tier={tone}>
      <div className="flex items-baseline gap-2">
        <span className="data-figure text-5xl font-semibold" style={{ color: `var(--color-${tone})` }}>
          {riskScore ?? "—"}
        </span>
        <span className="text-sm text-ink-faint">/ 100 overall risk</span>
      </div>

      <div className="mt-5">
        {riskAnalysis ? (
          <ul className="flex flex-col gap-3">
            {SUB_SCORES.map(([key, label]) => (
              <li key={key}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-ink-muted">{label}</span>
                  <span className="data-figure font-medium text-ink">{riskAnalysis[key]}</span>
                </div>
                <Progress value={riskAnalysis[key]} tone={scoreTone(100 - riskAnalysis[key])} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState>
            Financial, operational, and business risk sub-scores aren't broken out for this
            investigation yet.
          </EmptyState>
        )}
      </div>
    </Card>
  );
}
