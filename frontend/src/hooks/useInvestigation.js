import { useQuery } from "@tanstack/react-query";
import { getInvestigationDetail, listInvestigations } from "../api/investigations";

export function useInvestigations() {
  return useQuery({
    queryKey: ["investigations"],
    queryFn: listInvestigations,
  });
}

export function useInvestigation(id) {
  return useQuery({
    queryKey: ["investigation", id],
    queryFn: () => getInvestigationDetail(id),
    enabled: Boolean(id),
  });
}
