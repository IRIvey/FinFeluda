import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { FloatingChatButton } from "./FloatingChatButton";

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

/**
 * `hideChatButton` is set by ChatPage -- a floating button that
 * navigates to the page you're already on is a dead click, not a
 * shortcut. Every other investigation-scoped page renders Sidebar,
 * so putting the button here (rather than in each page) is what makes
 * it appear everywhere without per-page wiring.
 */
export function Sidebar({ investigationId, companyName, hideChatButton = false }) {
  const base = `/investigations/${investigationId}`;
  const { pathname } = useLocation();
  const isOnRiskRoute = pathname.startsWith(`${base}/risks/`) || pathname === `${base}/red-flags`;
  const [riskOpen, setRiskOpen] = useState(isOnRiskRoute);

  return (
    <>
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
            <SidebarLink to={`${base}/summary`}>Executive Summary</SidebarLink>
            <SidebarLink to={`${base}/recommendations`}>Recommendations</SidebarLink>

            <button
              type="button"
              onClick={() => setRiskOpen((open) => !open)}
              aria-expanded={riskOpen}
              className="mt-3 flex items-center justify-between rounded-lg px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-faint transition-colors hover:bg-black/[0.03] hover:text-ink"
            >
              Risk analysis
              <motion.svg
                aria-hidden="true"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4 shrink-0 text-ink-muted"
                animate={{ rotate: riskOpen ? 90 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <path d="M7.5 4.5l6 5.5-6 5.5" />
              </motion.svg>
            </button>
            <AnimatePresence initial={false}>
              {riskOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="flex flex-col gap-1 pb-1">
                    <SidebarLink to={`${base}/red-flags`}>Red Flags</SidebarLink>
                    {RISK_CATEGORIES.map(({ category, label }) => (
                      <SidebarLink key={category} to={`${base}/risks/${category}`}>
                        {label}
                      </SidebarLink>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="mt-3 border-t border-line pt-3">
              <SidebarLink to={`${base}/chat`}>Ask AI</SidebarLink>
              <SidebarLink to={`${base}/report`}>Report</SidebarLink>
            </div>
          </nav>
        </div>
      </aside>
      {!hideChatButton && <FloatingChatButton investigationId={investigationId} />}
    </>
  );
}
