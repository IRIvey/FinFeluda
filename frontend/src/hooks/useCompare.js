import { useQueries, useQuery } from "@tanstack/react-query";
import { getInvestigationDetail } from "../api/investigations";
import { compareInvestigations } from "../api/compare";

export function useCompare(id1, id2) {
  const results = useQueries({
    queries: [id1, id2].map((id) => ({
      queryKey: ["investigation", id],
      queryFn: () => getInvestigationDetail(id),
      enabled: Boolean(id),
    })),
  });

  const [a, b] = results;

  const summaryQuery = useQuery({
    queryKey: ["compare", id1, id2],
    queryFn: () => compareInvestigations(id1, id2),
    enabled: Boolean(id1 && id2),
  });

  return {
    investigationA: a?.data,
    investigationB: b?.data,
    isLoading: Boolean(id1 && id2) && (a?.isLoading || b?.isLoading),
    isError: a?.isError || b?.isError,
    summary: summaryQuery.data,
  };
}
