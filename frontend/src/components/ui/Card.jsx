import { cn } from "../../lib/utils";

/**
 * `tier` accepts a design-token color name (e.g. "tier-1", "risk-high")
 * and renders it as a left-edge bar — the evidence-ledger signature
 * used throughout the investigation dashboard so a card's evidentiary
 * weight or severity is visible at a glance, not just in its text.
 */
export function Card({ title, footer, tier, className, children, ...props }) {
  return (
    <div
      className={cn(
        "glass-card relative overflow-hidden",
        tier && "pl-[calc(1.5rem-3px)]",
        className
      )}
      {...props}
    >
      {tier && (
        <span
          aria-hidden="true"
          className="absolute left-0 top-0 h-full w-[3px]"
          style={{ backgroundColor: `var(--color-${tier})` }}
        />
      )}
      {title && (
        <div className="border-b border-line px-6 py-4">
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
        </div>
      )}
      <div className={cn(!title && !footer && "p-6", title && "p-6", "empty:p-0")}>{children}</div>
      {footer && <div className="border-t border-line px-6 py-4">{footer}</div>}
    </div>
  );
}
