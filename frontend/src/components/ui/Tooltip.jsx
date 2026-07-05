import { useState } from "react";
import { cn } from "../../lib/utils";

export function Tooltip({ content, children, className }) {
  const [open, setOpen] = useState(false);

  if (!content) return children;

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      {open && (
        <span
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 z-20 mb-2 w-max max-w-xs -translate-x-1/2 rounded-md bg-ink px-2.5 py-1.5 text-xs text-white shadow-card-hover",
            className
          )}
        >
          {content}
        </span>
      )}
    </span>
  );
}
