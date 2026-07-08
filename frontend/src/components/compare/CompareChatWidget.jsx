import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import chatImg from "../../assets/chat.png";
import { cn } from "../../lib/utils";
import { ChatWindow } from "../chat/ChatWindow";
import { ChatInput } from "../chat/ChatInput";
import { useComparisonChat } from "../../hooks/useComparisonChat";

/**
 * Floating "Ask AI" widget for the Compare page. Deliberately not a
 * page-link like FloatingChatButton (there's no single investigation
 * to navigate to here) -- it opens an inline panel instead, and is
 * strictly scoped to whichever two investigations are currently
 * selected in the Company A / Company B dropdowns. See
 * comparison_chat_service on the backend for why it never reaches for
 * a third company or outside data.
 */
export function CompareChatWidget({
  investigationIdA,
  investigationIdB,
  companyNameA,
  companyNameB,
}) {
  const [open, setOpen] = useState(false);
  const bothSelected = Boolean(investigationIdA && investigationIdB);
  const { messages, sendMessage, isSending, isHistoryLoading } = useComparisonChat(
    investigationIdA,
    investigationIdB
  );

  const labelA = companyNameA || "Company A";
  const labelB = companyNameB || "Company B";

  return (
    <>
      <motion.div
        initial={{ opacity: 0, scale: 0.7, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3, ease: "easeOut" }}
        className="fixed right-6 bottom-6 z-40"
      >
        {bothSelected && !open && (
          <motion.span
            aria-hidden="true"
            className="absolute inset-0 rounded-full bg-brand"
            animate={{ opacity: [0.35, 0, 0.35], scale: [1, 1.35, 1] }}
            transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
          />
        )}
        <button
          type="button"
          onClick={() => bothSelected && setOpen((v) => !v)}
          aria-label={
            bothSelected ? "Ask AI to compare these two companies" : "Select two companies first"
          }
          className={cn(
            "group relative flex h-14 w-14 items-center justify-center rounded-full shadow-card-hover transition-transform",
            bothSelected ? "bg-brand hover:scale-105" : "cursor-not-allowed bg-ink-faint/40"
          )}
        >
          <img
            src={chatImg}
            alt=""
            className="h-7 w-7"
            style={{ filter: "brightness(0) invert(1)" }}
          />
          <span className="pointer-events-none absolute right-full top-1/2 mr-3 -translate-y-1/2 whitespace-nowrap rounded-md bg-ink px-2.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-card-hover transition-opacity group-hover:opacity-100">
            {bothSelected ? "Ask AI to compare" : "Select two companies first"}
          </span>
        </button>
      </motion.div>

      <AnimatePresence>
        {open && bothSelected && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="glass-card fixed right-6 bottom-24 z-40 flex w-[26rem] max-w-[calc(100vw-3rem)] flex-col"
            style={{ height: "32rem" }}
          >
            <div className="flex items-center justify-between border-b border-line px-4 py-3">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand">Ask AI</p>
                <p className="truncate text-sm font-medium text-ink">
                  {labelA} vs {labelB}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close"
                className="rounded-md p-1 text-ink-faint hover:bg-black/[0.03] hover:text-ink"
              >
                ✕
              </button>
            </div>
            <ChatWindow
              messages={messages}
              isHistoryLoading={isHistoryLoading}
              emptyTitle="Ask AI to compare these two companies"
              emptyHint={`"How do their revenues compare?", "Which one carries more risk?", "Summarize the key differences."`}
            />
            <ChatInput onSend={sendMessage} isSending={isSending} />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
