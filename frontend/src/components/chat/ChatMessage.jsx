import { useState } from "react";
import { Badge } from "../ui/Badge";
import { cn, CONFIDENCE_TIER_META } from "../../lib/utils";

export function ChatMessage({ role, content, sources, isError }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isUser = role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("flex max-w-[85%] flex-col gap-2", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-brand text-white"
              : isError
                ? "border border-risk-critical-soft bg-risk-critical-soft text-risk-critical"
                : "glass-card text-ink"
          )}
        >
          {content}
        </div>

        {!isUser && sources?.length > 0 && (
          <div className="w-full">
            <button
              type="button"
              onClick={() => setSourcesOpen((v) => !v)}
              className="text-xs font-medium text-ink-faint hover:text-brand"
            >
              {sourcesOpen ? "Hide" : "Show"} {sources.length} source
              {sources.length === 1 ? "" : "s"}
            </button>
            {sourcesOpen && (
              <ul className="mt-2 flex flex-col gap-2">
                {sources.map((source, index) => {
                  const tier = CONFIDENCE_TIER_META[source.confidence_tier] ?? CONFIDENCE_TIER_META[4];
                  return (
                    <li key={index} className="glass-card p-3 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-ink">
                          {source.company && (
                            <span className="mr-1.5 text-ink-faint">[{source.company}]</span>
                          )}
                          {source.source_name}
                        </span>
                        <Badge color={tier.color}>{tier.label}</Badge>
                      </div>
                      <p className="mt-1 text-ink-muted">{source.excerpt}</p>
                      {source.origin_url && (
                        <a
                          href={source.origin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 inline-block text-brand hover:text-brand-deep"
                        >
                          View source →
                        </a>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
