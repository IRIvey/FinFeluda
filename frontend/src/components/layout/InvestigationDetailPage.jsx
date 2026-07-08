import { PageWrapper } from "./PageWrapper";
import { Sidebar } from "./Sidebar";
import { Card } from "../ui/Card";
import { Skeleton } from "../ui/Skeleton";
import { useInvestigation } from "../../hooks/useInvestigation";

/**
 * Shared loading/error/header boilerplate for the single-section
 * sidebar pages (red flags, executive summary, recommendations) --
 * same pattern RiskCategoryPage uses. `children` is a render prop so
 * each page can pull whatever it needs off the loaded investigation.
 */
export function InvestigationDetailPage({ id, eyebrow, title, children }) {
  const { data: investigation, isLoading, isError, error } = useInvestigation(id);

  if (isLoading || !investigation) {
    return (
      <PageWrapper>
        <div className="flex flex-col gap-4">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-32 w-full" />
        </div>
      </PageWrapper>
    );
  }

  if (isError) {
    return (
      <PageWrapper className="max-w-xl">
        <Card tier="risk-critical">
          <p className="font-medium text-ink">Couldn't load this investigation.</p>
          <p className="mt-1 text-sm text-ink-muted">{error?.message}</p>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">{eyebrow}</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">{title}</h1>
        <p className="mt-1 text-sm text-ink-faint">{investigation.company_name}</p>
      </div>

      <div className="flex gap-8">
        <Sidebar investigationId={id} companyName={investigation.company_name} />
        <div className="flex min-w-0 flex-1 flex-col gap-6">{children(investigation)}</div>
      </div>
    </PageWrapper>
  );
}
