import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";

export function Sidebar({ investigationId, companyName }) {
  const links = [
    { to: `/investigations/${investigationId}`, label: "Overview", end: true },
    { to: `/investigations/${investigationId}/chat`, label: "Ask AI" },
    { to: `/investigations/${investigationId}/report`, label: "Report" },
  ];

  return (
    <aside className="hidden w-48 shrink-0 md:block">
      <div className="sticky top-24">
        {companyName && (
          <p className="mb-3 truncate px-3 text-xs font-medium uppercase tracking-wide text-ink-faint">
            {companyName}
          </p>
        )}
        <nav className="flex flex-col gap-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-soft text-brand-deep"
                    : "text-ink-muted hover:bg-black/[0.03] hover:text-ink"
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
}
