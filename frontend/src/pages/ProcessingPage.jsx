import { useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { Progress } from "../components/ui/Progress";
import { usePolling } from "../hooks/usePolling";
import { triggerAnalyze } from "../api/analyze";

/**
 * `gathered` is a known dead end today: `/upload/` only runs GATHER +
 * NORMALIZE, and nothing currently auto-triggers the REASON stage that
 * would move status to `analyzing`/`completed` (see api/analyze.js).
 * Rather than spin forever pretending analysis is coming, this step
 * says so plainly and offers a way to see what's already there.
 */
const STEPS = [
  { status: "pending", step: 1, message: "Reading document…" },
  { status: "processing", step: 2, message: "Extracting financial tables…" },
  { status: "gathered", step: 3, message: "Data gathered — waiting for analysis" },
  { status: "analyzing", step: 4, message: "Generating report…" },
  { status: "completed", step: 5, message: "Creating dashboard…" },
];

const STEP_BY_STATUS = Object.fromEntries(STEPS.map((s) => [s.status, s]));
const TOTAL_STEPS = STEPS.length;

export function ProcessingPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error } = usePolling(id);
  const status = data?.status;

  // Restarting the poll after a retry matters: usePolling stops
  // refetching once it sees a terminal status, so without an
  // invalidation the page would sit on "failed" forever even though
  // the backend is already re-analyzing.
  const retry = useMutation({
    mutationFn: () => triggerAnalyze(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["investigation-status", id] }),
  });

  useEffect(() => {
    if (status === "completed") {
      navigate(`/investigations/${id}`, { replace: true });
    }
  }, [status, id, navigate]);

  if (isLoading) {
    return (
      <PageWrapper className="max-w-xl">
        <Card className="flex flex-col items-center gap-3 py-16 text-center">
          <Spinner size="lg" />
          <p className="text-sm text-ink-muted">Checking on this investigation…</p>
        </Card>
      </PageWrapper>
    );
  }

  if (isError) {
    return (
      <PageWrapper className="max-w-xl">
        <Card tier="risk-critical" className="flex flex-col items-center gap-3 py-12 text-center">
          <p className="font-display text-xl text-ink">Couldn't check on this investigation</p>
          <p className="text-sm text-ink-muted">{error?.message}</p>
          <Button as={Link} to="/dashboard" variant="secondary" className="mt-2">
            Back to dashboard
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  if (status === "failed") {
    return (
      <PageWrapper className="max-w-xl">
        <Card tier="risk-critical" className="flex flex-col items-center gap-3 py-12 text-center">
          <p className="font-display text-xl text-ink">This investigation failed</p>
          {data?.error_message ? (
            <>
              <p className="max-w-sm text-sm text-ink-muted">
                Analysis stopped partway through. The gathered data is still stored, so
                retrying won't re-upload anything.
              </p>
              <p className="max-w-md rounded-lg bg-risk-critical-soft px-4 py-3 text-left font-mono text-xs break-words text-risk-critical">
                {data.error_message}
              </p>
            </>
          ) : (
            <p className="max-w-sm text-sm text-ink-muted">
              None of the sources we tried — uploaded documents or public data — produced usable
              content. Try again with a different document or a company website.
            </p>
          )}
          {retry.isError && (
            <p className="max-w-sm text-xs text-risk-critical">
              Retry failed: {retry.error?.response?.data?.detail || retry.error?.message}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
            <Button onClick={() => retry.mutate()} isLoading={retry.isPending} variant="primary">
              Retry analysis
            </Button>
            <Button as={Link} to="/new" variant="secondary">
              Start a new investigation
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const current = STEP_BY_STATUS[status] ?? STEPS[0];

  return (
    <PageWrapper className="max-w-xl">
      <Card className="flex flex-col items-center gap-6 py-12 text-center">
        {status !== "gathered" && <Spinner size="lg" />}

        <div>
          <p className="font-display text-xl text-ink">{current.message}</p>
          {data?.company_name && (
            <p className="mt-1 text-sm text-ink-faint">{data.company_name}</p>
          )}
        </div>

        <Progress value={current.step} max={TOTAL_STEPS} className="w-full max-w-xs" />

        {status === "gathered" && (
          <div className="flex flex-col items-center gap-3">
            <p className="max-w-sm text-sm text-ink-muted">
              We've gathered evidence from every available source. The deeper AI analysis
              (financial extraction, risk scoring, executive summary) hasn't run for this
              investigation yet.
            </p>
            <Button as={Link} to={`/investigations/${id}`} variant="secondary">
              View partial results
            </Button>
          </div>
        )}
      </Card>
    </PageWrapper>
  );
}
