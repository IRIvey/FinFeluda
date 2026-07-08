import { useNavigate } from "react-router-dom";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ScoreRing } from "../charts/ScoreRing";
import { SubscoreBarChart } from "../charts/SubscoreBarChart";
import { scoreTone } from "../../lib/utils";

const SUB_SCORES = [
  ["financial_risk_score", "financial", "Financial"],
  ["operational_risk_score", "operational", "Operational"],
  ["business_risk_score", "business", "Business"],
];

export function RiskAnalysisPanel({ investigationId, riskScore, riskAnalysis }) {
  const navigate = useNavigate();
  const tone = scoreTone(100 - (riskScore ?? 50));

  return (
    <Card title="Risk analysis" tier={tone}>
      <div className="flex items-center gap-4">
        <ScoreRing value={riskScore} tone={tone} label="/ 100" />
        <div className="min-w-0 flex-1">
          {riskAnalysis ? (
            <SubscoreBarChart
              height={150}
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
      </div>
    </Card>
  );
}
