import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 15_000,
      refetchOnWindowFocus: false,
      // Some browser/automation contexts misreport connectivity, which
      // makes TanStack's default "online" network mode pause retries
      // indefinitely instead of settling to an error the UI can show.
      // "always" attempts every fetch regardless of that signal.
      networkMode: "always",
    },
  },
});
