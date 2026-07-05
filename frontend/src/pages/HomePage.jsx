import { Link } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { InvestigationCard } from "../components/investigation/InvestigationCard";
import { useInvestigations } from "../hooks/useInvestigation";

export function HomePage() {
  const { data: investigations, isLoading, isError, error } = useInvestigations();

  return (
    <PageWrapper>
      <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Dashboard</p>
          <h1 className="mt-1 font-display text-3xl font-semibold text-ink">
            Your investigations
          </h1>
          <p className="mt-2 max-w-xl text-sm text-ink-muted">
            Upload a document or point at a company's public footprint — the AI gathers evidence,
            scores it, and flags what needs a second look.
          </p>
        </div>
        <Button as={Link} to="/new" variant="primary" size="lg">
          New investigation
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="flex flex-col gap-4">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-3 w-1/3" />
              <div className="flex gap-8">
                <Skeleton className="h-8 w-12" />
                <Skeleton className="h-8 w-12" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {isError && (
        <Card tier="risk-critical">
          <p className="font-medium text-ink">Couldn't load investigations.</p>
          <p className="mt-1 text-sm text-ink-muted">{error?.message}</p>
        </Card>
      )}

      {!isLoading && !isError && investigations?.length === 0 && (
        <Card className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="font-display text-xl text-ink">No investigations yet</p>
          <p className="max-w-sm text-sm text-ink-muted">
            Start one by uploading a document or entering a company's website — the first report
            takes a few minutes to gather.
          </p>
          <Button as={Link} to="/new" variant="primary" className="mt-2">
            New investigation
          </Button>
        </Card>
      )}

      {!isLoading && !isError && investigations?.length > 0 && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {investigations.map((investigation) => (
            <InvestigationCard key={investigation.id} investigation={investigation} />
          ))}
        </div>
      )}
    </PageWrapper>
  );
}
