import { useNavigate } from "react-router-dom";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { SubscoreBarChart } from "../charts/SubscoreBarChart";
import { scoreTone } from "../../lib/utils";

const SUB_SCORES = [
  ["financial_risk_score", "financial", "Financial risk"],
  ["operational_risk_score", "operational", "Operational risk"],
  ["business_risk_score", "business", "Business risk"],
];

export function RiskAnalysisPanel({ investigationId, riskScore, riskAnalysis }) {
  const navigate = useNavigate();
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
          <SubscoreBarChart
            height={140}
            data={SUB_SCORES.map(([key, category, label]) => ({
              label,
              value: riskAnalysis[key],
              tone: scoreTone(100 - riskAnalysis[key]),
              onClick: () => navigate(`/investigations/${investigationId}/risks/${category}`),
            }))}
          />
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
