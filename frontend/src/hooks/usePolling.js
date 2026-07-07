import { useQuery } from "@tanstack/react-query";
import { getInvestigationStatus } from "../api/investigations";

const TERMINAL_STATUSES = new Set(["completed", "failed"]);

export function usePolling(id) {
  return useQuery({
    queryKey: ["investigation-status", id],
    queryFn: () => getInvestigationStatus(id),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && TERMINAL_STATUSES.has(status) ? false : 2000;
    },
    // Keep polling even if the user switches tabs mid-processing — this
    // can take minutes, and pausing on blur (TanStack's default) would
    // leave the page stuck showing a stale step when they switch back.
    refetchIntervalInBackground: true,
  });
}
