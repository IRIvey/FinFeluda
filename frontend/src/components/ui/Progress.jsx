import { cn } from "../../lib/utils";

export function Progress({ value = 0, max = 100, className, tone = "brand" }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-line", className)}>
      <div
        className="h-full rounded-full transition-[width] duration-500 ease-out"
        style={{ width: `${pct}%`, backgroundColor: `var(--color-${tone})` }}
      />
    </div>
  );
}
