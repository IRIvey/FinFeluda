import { useParams } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Sidebar } from "../components/layout/Sidebar";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { useInvestigation, useInvestigationSources } from "../hooks/useInvestigation";
import { CONFIDENCE_TIER_META, buildExploreLinks, formatSourceType } from "../lib/utils";

const TIER_DESCRIPTIONS = {
  1: "The company's own uploaded documents and official filings (e.g. SEC 10-Ks). The AI treats hard financial figures from these as fact.",
  2: "The company's own website, GitHub org, or verified business listings. Official, but not independently audited.",
  3: "Independent news coverage, Wikipedia, and general web search. Useful for cross-checking claims, not treated as verified financial data.",
  4: "Social media, forums, and community chatter (Reddit, YouTube, Glassdoor). Signal, not fact — the AI flags it as unverified.",
};

export function SourcesPage() {
  const { id } = useParams();
  const { data: investigation } = useInvestigation(id);
  const { data: sources, isLoading, isError, error } = useInvestigationSources(id);

  const byTier = {};
  for (const source of sources ?? []) {
    (byTier[source.confidence_tier] ??= []).push(source);
  }
  const tiers = Object.keys(byTier)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <PageWrapper>
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">Sources</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">
          {investigation?.company_name || "This investigation"}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-muted">
          Every place the AI actually looked while researching this company. Follow any link
          below to see the original material yourself.
        </p>
      </div>

      <div className="flex gap-8">
        <Sidebar investigationId={id} companyName={investigation?.company_name} />

        <div className="flex min-w-0 flex-1 flex-col gap-6">
          {isLoading && (
            <div className="flex flex-col gap-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          )}

          {isError && (
            <Card tier="risk-critical">
              <p className="font-medium text-ink">Couldn't load sources.</p>
              <p className="mt-1 text-sm text-ink-muted">{error?.message}</p>
            </Card>
          )}

          {!isLoading && !isError && (sources?.length ?? 0) === 0 && (
            <Card>
              <EmptyState>
                No sources have been gathered for this investigation yet.
              </EmptyState>
            </Card>
          )}

          {tiers.map((tier) => {
            const meta = CONFIDENCE_TIER_META[tier] ?? CONFIDENCE_TIER_META[4];
            return (
              <Card key={tier} tier={meta.color}>
                <div className="mb-4 flex items-center gap-2">
                  <Badge color={meta.color}>
                    Tier {tier} · {meta.label}
                  </Badge>
                </div>
                <p className="mb-4 text-sm text-ink-muted">{TIER_DESCRIPTIONS[tier]}</p>

                <ul className="flex flex-col divide-y divide-line">
                  {byTier[tier].map((source, index) => (
                    <li
                      key={index}
                      className="flex flex-wrap items-center justify-between gap-2 py-3 first:pt-0 last:pb-0"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium text-ink">{source.source_name}</p>
                        <p className="text-xs text-ink-faint">
                          {formatSourceType(source.source_type)} · {source.chunk_count} excerpt
                          {source.chunk_count === 1 ? "" : "s"} used
                        </p>
                      </div>
                      {source.origin_url ? (
                        <a
                          href={source.origin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 text-sm font-medium text-brand hover:text-brand-deep"
                        >
                          Visit source →
                        </a>
                      ) : (
                        <span className="shrink-0 text-xs text-ink-faint">
                          No direct link available
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </Card>
            );
          })}

          {investigation?.company_name && (
            <Card title="Explore more">
              <p className="mb-4 text-sm text-ink-muted">
                Places the AI didn't check itself — most social platforms block automated
                scraping without a paid API. These are direct search links, not analyzed
                content, in case they turn up something useful.
              </p>
              <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {buildExploreLinks(investigation.company_name).map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-lg border border-line px-3.5 py-2.5 transition-colors hover:border-brand hover:bg-brand-soft/40"
                    >
                      <p className="text-sm font-medium text-ink">{link.label}</p>
                      <p className="mt-0.5 text-xs text-ink-faint">{link.hint}</p>
                    </a>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
