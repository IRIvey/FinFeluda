import { Link } from "react-router-dom";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { formatDate, scoreTone, STATUS_META } from "../../lib/utils";

function ScorePair({ label, value }) {
  const tone = scoreTone(value);
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-ink-faint">{label}</p>
      <p className="data-figure text-2xl font-semibold" style={{ color: `var(--color-${tone})` }}>
        {value ?? "—"}
      </p>
    </div>
  );
}

export function InvestigationCard({ investigation }) {
  const status = STATUS_META[investigation.status] ?? STATUS_META.pending;
  const linkTarget =
    investigation.status === "completed" || investigation.status === "gathered"
      ? `/investigations/${investigation.id}`
      : `/investigations/${investigation.id}/processing`;

  return (
    <Card tier={status.color} className="flex flex-col gap-4 transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-display text-lg font-semibold text-ink">
            {investigation.company_name || "Untitled investigation"}
          </h3>
          <p className="mt-0.5 text-xs text-ink-faint">
            Uploaded {formatDate(investigation.created_at)}
          </p>
        </div>
        <Badge color={status.color}>{status.label}</Badge>
      </div>

      <div className="flex gap-8">
        <ScorePair label="Health score" value={investigation.health_score} />
        <ScorePair label="Risk score" value={investigation.risk_score} />
      </div>

      <Link
        to={linkTarget}
        className="mt-auto text-sm font-medium text-brand hover:text-brand-deep"
      >
        View details →
      </Link>
    </Card>
  );
}
