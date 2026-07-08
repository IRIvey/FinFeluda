import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { DistributionBar } from "../charts/DistributionBar";

const CATEGORY_COLOR = {
  investment: "tier-1",
  business: "tier-2",
  financial: "tier-3",
  operational: "tier-4",
};

export function RecommendationsPanel({ recommendations }) {
  const hasData = Array.isArray(recommendations) && recommendations.length > 0;

  return (
    <Card title="Recommendations">
      {!hasData ? (
        <EmptyState>No recommendations have been generated for this investigation yet.</EmptyState>
      ) : (
        <>
          <DistributionBar
            className="mb-5"
            segments={Object.entries(CATEGORY_COLOR).map(([category, color]) => ({
              label: category.charAt(0).toUpperCase() + category.slice(1),
              color,
              value: recommendations.filter((r) => r.category === category).length,
            }))}
          />
          <ul className="flex flex-col gap-4">
            {recommendations.map((rec, index) => (
              <li key={index} className="border-b border-line pb-4 last:border-0 last:pb-0">
                <Badge color={CATEGORY_COLOR[rec.category] ?? "tier-4"} className="capitalize">
                  {rec.category}
                </Badge>
                <p className="mt-2 text-sm font-medium text-ink">{rec.recommendation}</p>
                <p className="mt-1 text-sm text-ink-muted">{rec.rationale}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}
