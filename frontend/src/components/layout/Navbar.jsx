import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";
import { BrandMark } from "./BrandMark";

const LINKS = [
  { to: "/dashboard", label: "Dashboard", end: true },
  { to: "/new", label: "New Investigation" },
  { to: "/compare", label: "Compare" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/85 backdrop-blur-sm">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-6 py-2 md:px-8">
        <NavLink to="/" className="flex items-center gap-2.5">
          <BrandMark tagline />
        </NavLink>

        <nav className="flex items-center gap-1">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-2.5 py-2 text-sm font-medium whitespace-nowrap transition-colors sm:px-3",
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
    </header>
  );
}
