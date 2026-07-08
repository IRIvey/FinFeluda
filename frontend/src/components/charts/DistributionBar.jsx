/**
 * Compact stacked bar summarizing counts across a small set of
 * categories (severity, recommendation type, etc.) -- an at-a-glance
 * visual to sit above a text-heavy list, not a replacement for it.
 */
export function DistributionBar({ segments, className }) {
  const present = segments.filter((s) => s.value > 0);
  const total = present.reduce((sum, s) => sum + s.value, 0);
  if (total === 0) return null;

  return (
    <div className={className}>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-line">
        {present.map((s) => (
          <div
            key={s.label}
            title={`${s.value} ${s.label}`}
            style={{ width: `${(s.value / total) * 100}%`, backgroundColor: `var(--color-${s.color})` }}
          />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        {present.map((s) => (
          <span key={s.label} className="flex items-center gap-1.5 text-xs text-ink-muted">
            <span
              aria-hidden="true"
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: `var(--color-${s.color})` }}
            />
            <span className="data-figure font-medium text-ink">{s.value}</span> {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}
