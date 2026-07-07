import { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";

export function ChatWindow({ messages, isHistoryLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  if (isHistoryLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-1 text-center">
        <p className="text-sm text-ink-muted">Loading conversation...</p>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-1 text-center">
        <p className="font-display text-lg text-ink">Ask AI about this company</p>
        <p className="max-w-sm text-sm text-ink-muted">
          "Why did profit decrease?", "What are the biggest risks?", "Summarize cash flow."
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
      {messages.map((message, index) => (
        <ChatMessage key={index} {...message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
