import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { DistributionBar } from "../charts/DistributionBar";
import { SEVERITY_META } from "../../lib/utils";

const SEVERITY_ORDER = ["low", "medium", "high", "critical"];

export function RedFlagSection({ redFlags }) {
  const hasFlags = Array.isArray(redFlags) && redFlags.length > 0;

  return (
    <Card title="Red flags">
      {!hasFlags ? (
        <EmptyState>No red flags have been identified for this investigation yet.</EmptyState>
      ) : (
        <>
          <DistributionBar
            className="mb-5"
            segments={SEVERITY_ORDER.map((sev) => ({
              label: SEVERITY_META[sev].label,
              color: SEVERITY_META[sev].color,
              value: redFlags.filter((f) => f.severity === sev).length,
            }))}
          />
          <ul className="flex flex-col gap-4">
            {redFlags.map((flag, index) => {
              const severity = SEVERITY_META[flag.severity] ?? SEVERITY_META.medium;
              return (
                <li key={index}>
                  <Card tier={severity.color} padding="sm">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-medium text-ink">{flag.title}</p>
                      <div className="flex gap-1.5">
                        {flag.is_contradiction && <Badge color="tier-3">Contradiction</Badge>}
                        <Badge color={severity.color}>{severity.label}</Badge>
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-ink-muted">{flag.reason}</p>
                    <p className="mt-2 text-sm">
                      <span className="font-medium text-ink">Recommendation: </span>
                      <span className="text-ink-muted">{flag.recommendation}</span>
                    </p>
                    {flag.supporting_sources?.length > 0 && (
                      <p className="mt-2 text-xs text-ink-faint">
                        Sources: {flag.supporting_sources.join(", ")}
                      </p>
                    )}
                  </Card>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </Card>
  );
}
