import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ScoreRing } from "../charts/ScoreRing";
import { SubscoreBarChart } from "../charts/SubscoreBarChart";
import { scoreTone } from "../../lib/utils";

const SUBSCORE_LABELS = ["growth", "liquidity", "profitability", "debt", "efficiency"];

export function HealthScoreCard({ healthScore, subscores }) {
  const tone = scoreTone(healthScore);

  return (
    <Card title="Financial health score" tier={tone}>
      <div className="flex items-center gap-4">
        <ScoreRing value={healthScore} tone={tone} label="/ 100" />
        <div className="min-w-0 flex-1">
          {subscores ? (
            <SubscoreBarChart
              height={150}
              data={SUBSCORE_LABELS.filter((key) => subscores[key] !== undefined).map((key) => ({
                label: key.charAt(0).toUpperCase() + key.slice(1),
                value: subscores[key],
                tone: scoreTone(subscores[key]),
              }))}
            />
          ) : (
            <EmptyState>
              Growth, liquidity, profitability, debt, and efficiency sub-scores aren't broken out
              for this investigation yet.
            </EmptyState>
          )}
        </div>
      </div>
    </Card>
  );
}
