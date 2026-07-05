export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function formatCurrency(value, currency = "USD") {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: Math.abs(value) >= 1_000_000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatNumber(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

export const STATUS_META = {
  pending: { label: "Pending", color: "tier-4" },
  processing: { label: "Processing", color: "tier-2" },
  gathered: { label: "Gathered", color: "tier-3" },
  analyzing: { label: "Analyzing", color: "tier-2" },
  completed: { label: "Completed", color: "tier-1" },
  failed: { label: "Failed", color: "risk-critical" },
};

export const SEVERITY_META = {
  low: { label: "Low", color: "risk-low" },
  medium: { label: "Medium", color: "risk-medium" },
  high: { label: "High", color: "risk-high" },
  critical: { label: "Critical", color: "risk-critical" },
};

export const CONFIDENCE_TIER_META = {
  1: { label: "Authoritative", color: "tier-1" },
  2: { label: "Official", color: "tier-2" },
  3: { label: "Corroborating", color: "tier-3" },
  4: { label: "Unverified signal", color: "tier-4" },
};

export function scoreTone(score) {
  if (score === null || score === undefined) return "tier-4";
  if (score >= 75) return "tier-1";
  if (score >= 50) return "tier-3";
  return "risk-critical";
}
