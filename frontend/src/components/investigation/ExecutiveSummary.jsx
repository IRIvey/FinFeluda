import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";

const SECTIONS = [
  ["company_summary", "Company summary"],
  ["financial_summary", "Financial summary"],
  ["major_risks", "Major risks"],
  ["opportunities", "Opportunities"],
  ["future_outlook", "Future outlook"],
];

export function ExecutiveSummary({ summary }) {
  return (
    <Card title="Executive summary">
      {!summary ? (
        <EmptyState>The AI executive summary hasn't been generated for this investigation yet.</EmptyState>
      ) : (
        <div className="flex flex-col gap-5">
          {SECTIONS.filter(([key]) => summary[key]).map(([key, label]) => (
            <div key={key}>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand">{label}</p>
              <p className="mt-1 text-sm leading-relaxed text-ink">{summary[key]}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
