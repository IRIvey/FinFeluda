import { useParams } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Sidebar } from "../components/layout/Sidebar";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { CompanyOverview } from "../components/investigation/CompanyOverview";
import { FinancialDashboard } from "../components/investigation/FinancialDashboard";
import { HealthScoreCard } from "../components/investigation/HealthScoreCard";
import { RiskAnalysisPanel } from "../components/investigation/RiskAnalysisPanel";
import { CompanyTimeline } from "../components/investigation/CompanyTimeline";
import { ReportDownloadButton } from "../components/investigation/ReportDownloadButton";
import { useInvestigation } from "../hooks/useInvestigation";
import { STATUS_META } from "../lib/utils";

export function InvestigationPage() {
  const { id } = useParams();
  const { data: investigation, isLoading, isError, error } = useInvestigation(id);

  // Guard on `!investigation` too, not just `isLoading` — a query that
  // hasn't settled yet (e.g. still retrying) can have isLoading and
  // isError both false with no data, and this page must not crash on
  // `investigation.status` in that gap.
  if (isLoading || !investigation) {
    return (
      <PageWrapper>
        <div className="flex flex-col gap-4">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </PageWrapper>
    );
  }

  if (isError) {
    return (
      <PageWrapper className="max-w-xl">
        <Card tier="risk-critical" className="text-center">
          <p className="font-medium text-ink">Couldn't load this investigation.</p>
          <p className="mt-1 text-sm text-ink-muted">{error?.message}</p>
        </Card>
      </PageWrapper>
    );
  }

  const status = STATUS_META[investigation.status] ?? STATUS_META.pending;

  return (
    <PageWrapper>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-display text-3xl font-semibold text-ink">
              {investigation.company_name || "Untitled investigation"}
            </h1>
            <Badge color={status.color}>{status.label}</Badge>
          </div>
          <p className="mt-1 text-sm text-ink-faint">Source: {investigation.source_type}</p>
        </div>
        <ReportDownloadButton investigationId={id} companyName={investigation.company_name} />
      </div>

      <div className="flex gap-8">
        <Sidebar investigationId={id} companyName={investigation.company_name} />

        <div className="flex min-w-0 flex-1 flex-col gap-6">
          <CompanyOverview company={investigation.company} />

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <HealthScoreCard
              healthScore={investigation.health_score}
              subscores={investigation.health_subscores}
            />
            <RiskAnalysisPanel
              investigationId={id}
              riskScore={investigation.risk_score}
              riskAnalysis={investigation.risk_analysis}
            />
          </div>

          <FinancialDashboard financials={investigation.financials} />
          <CompanyTimeline financials={investigation.financials} />
        </div>
      </div>
    </PageWrapper>
  );
}
