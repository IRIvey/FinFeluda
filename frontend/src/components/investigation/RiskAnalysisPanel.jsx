import { Link } from "react-router-dom";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { Progress } from "../ui/Progress";
import { scoreTone } from "../../lib/utils";

const SUB_SCORES = [
  ["financial_risk_score", "financial", "Financial risk"],
  ["operational_risk_score", "operational", "Operational risk"],
  ["business_risk_score", "business", "Business risk"],
];

export function RiskAnalysisPanel({ investigationId, riskScore, riskAnalysis }) {
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
            {SUB_SCORES.map(([key, category, label]) => (
              <li key={key}>
                <Link
                  to={`/investigations/${investigationId}/risks/${category}`}
                  className="group block rounded-lg -mx-2 px-2 py-1.5 transition-colors hover:bg-black/[0.03]"
                >
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-ink-muted group-hover:text-ink">{label}</span>
                    <span className="flex items-center gap-1.5">
                      <span className="data-figure font-medium text-ink">{riskAnalysis[key]}</span>
                      <span className="text-brand opacity-0 transition-opacity group-hover:opacity-100">
                        →
                      </span>
                    </span>
                  </div>
                  <Progress value={riskAnalysis[key]} tone={scoreTone(100 - riskAnalysis[key])} />
                </Link>
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
