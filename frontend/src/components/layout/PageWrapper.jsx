import { cn } from "../../lib/utils";

export function PageWrapper({ className, children }) {
  return (
    <main className={cn("mx-auto w-full max-w-6xl px-6 py-10 md:px-8", className)}>
      {children}
    </main>
  );
}
