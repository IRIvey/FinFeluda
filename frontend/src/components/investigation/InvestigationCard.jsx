import { useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Modal } from "../ui/Modal";
import { useDeleteInvestigation } from "../../hooks/useInvestigation";
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
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const deleteInvestigation = useDeleteInvestigation();

  const status = STATUS_META[investigation.status] ?? STATUS_META.pending;
  const linkTarget =
    investigation.status === "completed" || investigation.status === "gathered"
      ? `/investigations/${investigation.id}`
      : `/investigations/${investigation.id}/processing`;

  const handleDelete = async () => {
    await deleteInvestigation.mutateAsync(investigation.id);
    setIsConfirmOpen(false);
  };

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
        <div className="flex shrink-0 items-center gap-2">
          <Badge color={status.color}>{status.label}</Badge>
          <button
            type="button"
            aria-label="Delete investigation"
            onClick={() => setIsConfirmOpen(true)}
            className="rounded-md p-1 text-ink-faint transition-colors hover:bg-black/[0.04] hover:text-risk-critical"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path
                fillRule="evenodd"
                d="M8.75 1a.75.75 0 0 0-.75.75V3H4a.75.75 0 0 0 0 1.5h.324l.777 10.877A2.75 2.75 0 0 0 7.844 18h4.312a2.75 2.75 0 0 0 2.743-2.623L15.676 4.5H16a.75.75 0 0 0 0-1.5h-4v-1.25a.75.75 0 0 0-.75-.75h-2.5ZM8.5 7.75a.75.75 0 0 1 1.5 0v6.5a.75.75 0 0 1-1.5 0v-6.5Zm3.75-.75a.75.75 0 0 0-.75.75v6.5a.75.75 0 0 0 1.5 0v-6.5a.75.75 0 0 0-.75-.75Z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
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

      <Modal
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        title="Delete investigation?"
      >
        <p className="text-sm text-ink-muted">
          This permanently deletes{" "}
          <span className="font-medium text-ink">
            {investigation.company_name || "this investigation"}
          </span>{" "}
          and all of its analysis, sources, and chat history. This can't be undone.
        </p>
        {deleteInvestigation.isError && (
          <p className="mt-3 text-sm text-risk-critical">{deleteInvestigation.error.message}</p>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" size="sm" onClick={() => setIsConfirmOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            size="sm"
            isLoading={deleteInvestigation.isPending}
            onClick={handleDelete}
          >
            Delete
          </Button>
        </div>
      </Modal>
    </Card>
  );
}
