/**
 * Literal hex mirror of index.css's @theme color tokens, for chart
 * libraries (recharts, hand-rolled SVG) that render outside React's
 * normal DOM diffing path -- that path doesn't reliably resolve CSS
 * custom properties passed as `fill="var(--color-x)"`.
 */
export const TONE_HEX = {
  "tier-1": "#0f6b5c",
  "tier-2": "#3e5c8a",
  "tier-3": "#b8752e",
  "tier-4": "#6b7078",
  "risk-low": "#3e5c8a",
  "risk-medium": "#b8752e",
  "risk-high": "#a3492a",
  "risk-critical": "#a32a2a",
};
