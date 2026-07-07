import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";

const RISK_CATEGORIES = [
  { category: "financial", label: "Financial" },
  { category: "operational", label: "Operational" },
  { category: "business", label: "Business" },
];

function SidebarLink({ to, end, children }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-brand-soft text-brand-deep"
            : "text-ink-muted hover:bg-black/[0.03] hover:text-ink"
        )
      }
    >
      {children}
    </NavLink>
  );
}

export function Sidebar({ investigationId, companyName }) {
  const base = `/investigations/${investigationId}`;

  return (
    <aside className="hidden w-48 shrink-0 md:block">
      <div className="sticky top-24">
        {companyName && (
          <p className="mb-3 truncate px-3 text-xs font-medium uppercase tracking-wide text-ink-faint">
            {companyName}
          </p>
        )}
        <nav className="flex flex-col gap-1">
          <SidebarLink to={base} end>
            Overview
          </SidebarLink>
          <SidebarLink to={`${base}/sources`}>Sources</SidebarLink>

          <p className="mb-1 mt-3 px-3 text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
            Risk analysis
          </p>
          {RISK_CATEGORIES.map(({ category, label }) => (
            <SidebarLink key={category} to={`${base}/risks/${category}`}>
              {label}
            </SidebarLink>
          ))}

          <div className="mt-3 border-t border-line pt-3">
            <SidebarLink to={`${base}/chat`}>Ask AI</SidebarLink>
            <SidebarLink to={`${base}/report`}>Report</SidebarLink>
          </div>
        </nav>
      </div>
    </aside>
  );
}
