import { cn } from "../../lib/utils";

const SIZES = {
  sm: "h-3.5 w-3.5 border-2",
  md: "h-5 w-5 border-2",
  lg: "h-8 w-8 border-[3px]",
};

export function Spinner({ size = "md", className }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        "inline-block animate-spin rounded-full border-current border-t-transparent text-brand",
        SIZES[size],
        className
      )}
    />
  );
}
