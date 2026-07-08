export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function formatCurrency(value, currency = "USD") {
  if (value === null || value === undefined) return "—";
  const isCompact = Math.abs(value) >= 1_000_000;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: isCompact ? "compact" : "standard",
    maximumFractionDigits: isCompact ? 1 : 0,
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

export const SENTIMENT_META = {
  positive: { label: "Positive", color: "tier-1" },
  negative: { label: "Negative", color: "risk-critical" },
  neutral: { label: "Neutral", color: "tier-4" },
  mixed: { label: "Mixed", color: "tier-3" },
};

export const CONFIDENCE_TIER_META = {
  1: { label: "Authoritative", color: "tier-1" },
  2: { label: "Official", color: "tier-2" },
  3: { label: "Corroborating", color: "tier-3" },
  4: { label: "Unverified signal", color: "tier-4" },
};

export function formatSourceType(type) {
  if (!type) return "Source";
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/**
 * Direct search links for platforms the backend doesn't (and largely
 * can't, without a paid API or app-review access) scrape automatically
 * -- Facebook, X/Twitter, and LinkedIn all restrict unauthenticated
 * search access. These are plain constructed search URLs, not analyzed
 * content, so the Sources page must label them as such rather than
 * imply the AI already looked at them.
 */
export function buildExploreLinks(companyName) {
  const q = encodeURIComponent(companyName);
  return [
    {
      label: "Facebook",
      url: `https://www.facebook.com/search/top?q=${q}`,
      hint: "Public posts, page updates, follower comments",
    },
    {
      label: "X / Twitter",
      url: `https://twitter.com/search?q=${q}`,
      hint: "Real-time sentiment, announcements, complaints",
    },
    {
      label: "LinkedIn",
      url: `https://www.linkedin.com/search/results/companies/?keywords=${q}`,
      hint: "Headcount, hiring activity, leadership profiles",
    },
    {
      label: "Instagram",
      url: `https://www.instagram.com/explore/search/keyword/?q=${q}`,
      hint: "Brand presence, product/marketing signal",
    },
    {
      label: "Crunchbase",
      url: `https://www.crunchbase.com/textsearch?q=${q}`,
      hint: "Funding history, investors, acquisitions",
    },
    {
      label: "Glassdoor",
      url: `https://www.glassdoor.com/Search/results.htm?keyword=${q}`,
      hint: "Employee reviews, culture, attrition signal",
    },
    {
      label: "Google",
      url: `https://www.google.com/search?q=${q}`,
      hint: "General web search for anything the above missed",
    },
  ];
}

export function scoreTone(score) {
  if (score === null || score === undefined) return "tier-4";
  if (score >= 75) return "tier-1";
  if (score >= 50) return "tier-3";
  return "risk-critical";
}
