import { Navigate, useParams } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Sidebar } from "../components/layout/Sidebar";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { DistributionBar } from "../components/charts/DistributionBar";
import { useInvestigation } from "../hooks/useInvestigation";
import { SEVERITY_META, scoreTone } from "../lib/utils";

const SEVERITY_ORDER = ["low", "medium", "high", "critical"];

const CATEGORY_META = {
  financial: {
    label: "Financial Risk",
    scoreKey: "financial_risk_score",
    description:
      "Risks visible in the numbers themselves — revenue decline, shrinking margins, mounting debt, cash flow problems, or gaps in financial disclosure. These are the risks a balance sheet and income statement reveal on their own.",
  },
  operational: {
    label: "Operational Risk",
    scoreKey: "operational_risk_score",
    description:
      "Risks in how the company actually runs day to day — engineering and product velocity, hiring and retention, supply chain, and execution capability. Often visible in public signal (GitHub activity, reviews, hiring pages) before it shows up in financials.",
  },
  business: {
    label: "Business Risk",
    scoreKey: "business_risk_score",
    description:
      "Risks to the business model and market position itself — competitive pressure, customer concentration, regulatory exposure, and whether the company's public claims match independent reality.",
  },
};

export function RiskCategoryPage() {
  const { id, category } = useParams();
  const meta = CATEGORY_META[category];
  const { data: investigation, isLoading, isError, error } = useInvestigation(id);

  if (!meta) {
    return <Navigate to={`/investigations/${id}`} replace />;
  }

  if (isLoading) {
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

  const score = investigation?.[meta.scoreKey];
  const tone = scoreTone(100 - (score ?? 50));
  const redFlags = (investigation?.risk_analysis?.red_flags ?? []).filter(
    (flag) => flag.category === category
  );

  return (
    <PageWrapper>
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">Risk Analysis</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">{meta.label}</h1>
        <p className="mt-1 text-sm text-ink-faint">{investigation?.company_name}</p>
      </div>

      <div className="flex gap-8">
        <Sidebar investigationId={id} companyName={investigation?.company_name} />

        <div className="flex min-w-0 flex-1 flex-col gap-6">
          <Card tier={tone}>
            <div className="flex items-baseline gap-2">
              <span
                className="data-figure text-5xl font-semibold"
                style={{ color: `var(--color-${tone})` }}
              >
                {score ?? "—"}
              </span>
              <span className="text-sm text-ink-faint">/ 100 {meta.label.toLowerCase()}</span>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-ink-muted">{meta.description}</p>
          </Card>

          <Card title={`${meta.label} findings`}>
            {redFlags.length === 0 ? (
              <EmptyState>
                No {meta.label.toLowerCase()} findings have been identified for this investigation
                yet.
              </EmptyState>
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
        </div>
      </div>
    </PageWrapper>
  );
}
