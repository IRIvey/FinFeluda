import { cn } from "../../lib/utils";

/** Small mono-caps pill. `color` maps to a design token, e.g. "tier-1", "risk-high". */
export function Badge({ color = "tier-4", children, className }) {
  return (
    <span
      className={cn("tier-tag", className)}
      style={{
        backgroundColor: `var(--color-${color}-soft, var(--color-line))`,
        color: `var(--color-${color})`,
      }}
    >
      {children}
    </span>
  );
}
