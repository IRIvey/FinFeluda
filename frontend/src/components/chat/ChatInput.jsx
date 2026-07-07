import { useState } from "react";
import { Button } from "../ui/Button";

export function ChatInput({ onSend, isSending }) {
  const [value, setValue] = useState("");

  const submit = () => {
    if (!value.trim() || isSending) return;
    onSend(value);
    setValue("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex items-end gap-3 border-t border-line p-4">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about this company's financials, risks, or filings…"
        rows={1}
        className="max-h-32 flex-1 resize-none rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-brand focus:outline-none"
      />
      <Button onClick={submit} isLoading={isSending} disabled={!value.trim()}>
        Send
      </Button>
    </div>
  );
}
