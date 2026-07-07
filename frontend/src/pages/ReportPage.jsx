import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Sidebar } from "../components/layout/Sidebar";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ReportDownloadButton } from "../components/investigation/ReportDownloadButton";
import { useInvestigation } from "../hooks/useInvestigation";
import { getReport } from "../api/report";

const SECTIONS = [
  ["executive_summary", "Executive summary"],
  ["financial_summary", "Financial summary"],
  ["risk_summary", "Risk summary"],
  ["opportunities", "Opportunities"],
  ["future_outlook", "Future outlook"],
  ["recommendations", "Recommendations"],
];

export function ReportPage() {
  const { id } = useParams();
  const { data: investigation } = useInvestigation(id);
  const { data: report, isLoading } = useQuery({
    queryKey: ["report", id],
    queryFn: () => getReport(id),
    enabled: Boolean(id),
  });

  // The backend's /report/{id} is currently a literal stub
  // (`{"report": "not implemented yet"}`), which doesn't match any
  // ReportOut field -- treat "no known section present" as "no report
  // yet" rather than rendering the stub's raw debug text.
  const hasReport = report && SECTIONS.some(([key]) => report[key]);

  return (
    <PageWrapper>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Report</p>
          <h1 className="mt-1 font-display text-3xl font-semibold text-ink">
            {investigation?.company_name || "This investigation"}
          </h1>
        </div>
        <ReportDownloadButton investigationId={id} pdfUrl={report?.pdf_url} />
      </div>

      <div className="flex gap-8">
        <Sidebar investigationId={id} companyName={investigation?.company_name} />

        <div className="min-w-0 flex-1">
          {isLoading ? (
            <div className="flex flex-col gap-4">
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : !hasReport ? (
            <Card>
              <EmptyState>
                The due diligence report hasn't been generated for this investigation yet.
              </EmptyState>
            </Card>
          ) : (
            <Card className="flex flex-col gap-6">
              {SECTIONS.filter(([key]) => report[key]).map(([key, label]) => (
                <div key={key}>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                    {label}
                  </p>
                  <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-ink">
                    {report[key]}
                  </p>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
