import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";

const FIELDS = [
  ["industry", "Industry"],
  ["headquarters", "Headquarters"],
  ["business_model", "Business model"],
  ["products", "Products"],
];

export function CompanyOverview({ company }) {
  return (
    <Card title="Company overview">
      {!company ? (
        <EmptyState>Company overview isn't available for this investigation yet.</EmptyState>
      ) : (
        <div className="flex flex-col gap-5">
          {company.summary && <p className="text-sm leading-relaxed text-ink">{company.summary}</p>}
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {FIELDS.filter(([key]) => company[key]).map(([key, label]) => (
              <div key={key}>
                <dt className="text-xs font-medium uppercase tracking-wide text-ink-faint">
                  {label}
                </dt>
                <dd className="mt-0.5 text-sm text-ink">{company[key]}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </Card>
  );
}
