import { useQuery } from "@tanstack/react-query";
import {
  getInvestigationDetail,
  getInvestigationSources,
  listInvestigations,
} from "../api/investigations";

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

export function useInvestigationSources(id) {
  return useQuery({
    queryKey: ["investigation-sources", id],
    queryFn: () => getInvestigationSources(id),
    enabled: Boolean(id),
  });
}
