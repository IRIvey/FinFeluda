import { cn } from "../../lib/utils";
import { Spinner } from "./Spinner";

const VARIANTS = {
  primary: "bg-brand text-white hover:bg-brand-deep",
  secondary: "bg-surface text-ink border border-line hover:border-line-strong",
  ghost: "bg-transparent text-ink-muted hover:text-ink hover:bg-black/[0.03]",
  danger: "bg-risk-critical text-white hover:opacity-90",
};

const SIZES = {
  sm: "text-sm px-3 py-1.5 gap-1.5",
  md: "text-sm px-4 py-2.5 gap-2",
  lg: "text-base px-5 py-3 gap-2",
};

export function Button({
  as: Component = "button",
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled = false,
  className,
  children,
  type,
  ...props
}) {
  const isButtonEl = Component === "button";
  return (
    <Component
      type={isButtonEl ? type ?? "button" : undefined}
      disabled={isButtonEl ? disabled || isLoading : undefined}
      aria-disabled={!isButtonEl && (disabled || isLoading) ? true : undefined}
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className
      )}
      {...props}
    >
      {isLoading && <Spinner size="sm" className={variant === "primary" ? "text-white" : ""} />}
      {children}
    </Component>
  );
}
