import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import { ComparisonChart } from "../components/charts/ComparisonChart";
import { useInvestigations } from "../hooks/useInvestigation";
import { useCompare } from "../hooks/useCompare";
import { cn, formatCurrency } from "../lib/utils";

const FINANCIAL_ROWS = [
  { key: "revenue", label: "Latest revenue" },
  { key: "profit", label: "Latest profit" },
  { key: "cash_flow", label: "Latest cash flow" },
  { key: "debt", label: "Latest debt", lowerIsBetter: true },
  { key: "expenses", label: "Latest expenses", lowerIsBetter: true },
];

function InvestigationSelect({ label, value, onChange, options }) {
  return (
    <div className="flex-1">
      <label className="text-sm font-medium text-ink">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink focus:border-brand focus:outline-none"
      >
        <option value="">Select an investigation…</option>
        {options.map((inv) => (
          <option key={inv.id} value={inv.id}>
            {inv.company_name || "Untitled investigation"}
          </option>
        ))}
      </select>
    </div>
  );
}

/** Which side wins a metric depends on whether lower is better (risk,
    debt) or higher is better (everything else) -- returns "A", "B",
    or null for a tie/missing data, so the table can bold the winner
    instead of making the reader compare two plain numbers themselves. */
function winner(valueA, valueB, lowerIsBetter = false) {
  if (valueA == null || valueB == null || valueA === valueB) return null;
  const aWins = lowerIsBetter ? valueA < valueB : valueA > valueB;
  return aWins ? "A" : "B";
}

/** Converts inline `**bold**` markdown into real <strong> text instead
    of leaving the literal asterisks in the rendered output. */
function renderInlineBold(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    const match = part.match(/^\*\*([^*]+)\*\*$/);
    return match ? (
      <strong key={i} className="font-semibold text-ink">
        {match[1]}
      </strong>
    ) : (
      part
    );
  });
}

/** The AI writes each point as "N. **Topic**: description" -- pull the
    topic out and render it bold and a step larger than the description,
    instead of showing the raw "**Topic**" markdown inline with the text. */
function ComparisonPoint({ text }) {
  const match = text.match(/^\s*(?:\d+\.\s*)?\*\*([^*]+)\*\*:?\s*([\s\S]*)$/);
  if (!match) {
    return <p className="text-sm leading-relaxed text-ink">{renderInlineBold(text)}</p>;
  }
  const [, topic, rest] = match;
  return (
    <div>
      <p className="text-base font-semibold text-ink">{topic}</p>
      {rest && <p className="mt-1 text-sm leading-relaxed text-ink-muted">{renderInlineBold(rest)}</p>}
    </div>
  );
}

function MetricCell({ value, format = (v) => v, isWinner }) {
  return (
    <td
      className={cn(
        "data-figure py-2 pr-4",
        isWinner ? "font-semibold text-tier-1" : "text-ink-muted"
      )}
    >
      {value == null ? "—" : format(value)}
      {isWinner && (
        <span aria-hidden="true" className="ml-1 text-xs">
          ▲
        </span>
      )}
    </td>
  );
}

export function ComparePage() {
  const [idA, setIdA] = useState("");
  const [idB, setIdB] = useState("");
  const [summaryOpen, setSummaryOpen] = useState(false);
  const { data: investigations } = useInvestigations();
  const { investigationA, investigationB, isLoading, summary } = useCompare(idA, idB);

  const bothSelected = Boolean(idA && idB);
  // The backend's /compare/ endpoint is currently a literal stub whose
  // response doesn't describe a real comparison -- show an honest
  // empty state instead of that raw debug string.
  const hasSummary = summary?.comparison && summary.comparison !== "not implemented yet";

  const nameOf = (inv) => inv?.company_name || "Untitled investigation";

  const latestFinancial = (inv) => {
    const financials = inv?.financials;
    if (!Array.isArray(financials) || financials.length === 0) return null;
    return [...financials].sort((a, b) => b.year - a.year)[0];
  };

  const finA = latestFinancial(investigationA);
  const finB = latestFinancial(investigationB);

  return (
    <PageWrapper>
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">Compare</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">
          Compare two investigations
        </h1>
      </div>

      <Card className="mb-6 flex flex-col gap-4 sm:flex-row">
        <InvestigationSelect label="Company A" value={idA} onChange={setIdA} options={investigations ?? []} />
        <InvestigationSelect label="Company B" value={idB} onChange={setIdB} options={investigations ?? []} />
      </Card>

      {!bothSelected && (
        <Card>
          <EmptyState>Select two investigations above to compare them.</EmptyState>
        </Card>
      )}

      {bothSelected && isLoading && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {bothSelected && !isLoading && investigationA && investigationB && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Card title="Health score comparison">
              <ComparisonChart
                data={[
                  {
                    metric: "Health score",
                    A: investigationA.health_score ?? 0,
                    B: investigationB.health_score ?? 0,
                  },
                ]}
                labelA={nameOf(investigationA)}
                labelB={nameOf(investigationB)}
              />
            </Card>
            <Card title="Risk score comparison">
              <ComparisonChart
                data={[
                  {
                    metric: "Risk score",
                    A: investigationA.risk_score ?? 0,
                    B: investigationB.risk_score ?? 0,
                  },
                ]}
                labelA={nameOf(investigationA)}
                labelB={nameOf(investigationB)}
              />
            </Card>
          </div>

          <Card title="Financials">
            <p className="mb-3 text-xs text-ink-faint">
              <span className="text-tier-1">▲</span> marks the stronger value in each row. Both
              companies' latest reported year, side by side.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-line text-xs uppercase tracking-wide text-ink-faint">
                    <th className="py-2 pr-4 font-medium">Metric</th>
                    <th className="py-2 pr-4 font-medium">{nameOf(investigationA)}</th>
                    <th className="py-2 font-medium">{nameOf(investigationB)}</th>
                  </tr>
                </thead>
                <tbody>
                  {FINANCIAL_ROWS.map(({ key, label, lowerIsBetter }, i) => (
                    <tr key={key} className={i < FINANCIAL_ROWS.length - 1 ? "border-b border-line" : ""}>
                      <td className="py-2 pr-4 text-ink-muted">{label}</td>
                      <MetricCell
                        value={finA?.[key]}
                        format={formatCurrency}
                        isWinner={winner(finA?.[key], finB?.[key], lowerIsBetter) === "A"}
                      />
                      <MetricCell
                        value={finB?.[key]}
                        format={formatCurrency}
                        isWinner={winner(finA?.[key], finB?.[key], lowerIsBetter) === "B"}
                      />
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="AI comparison summary">
            {!hasSummary ? (
              <EmptyState>An AI-generated comparison isn't available for these investigations yet.</EmptyState>
            ) : (
              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="px-0 hover:bg-transparent"
                  onClick={() => setSummaryOpen((open) => !open)}
                  aria-expanded={summaryOpen}
                >
                  {summaryOpen ? "Hide the full write-up" : "Read the full write-up"}
                  <motion.svg
                    aria-hidden="true"
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="ml-1 h-4 w-4"
                    animate={{ rotate: summaryOpen ? 90 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <path d="M7.5 4.5l6 5.5-6 5.5" />
                  </motion.svg>
                </Button>
                <p className="mt-1 text-xs text-ink-faint">
                  The scores and metrics above already summarize the numbers — this is the AI's
                  full written reasoning, if you want it.
                </p>
                <AnimatePresence initial={false}>
                  {summaryOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: "easeOut" }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 flex flex-col gap-4">
                        {summary.comparison
                          .split(/\n\s*\n/)
                          .map((s) => s.trim())
                          .filter(Boolean)
                          .map((block, i) => (
                            <ComparisonPoint key={i} text={block} />
                          ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </Card>
        </div>
      )}
    </PageWrapper>
  );
}
