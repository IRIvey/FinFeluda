import { apiClient } from "../lib/axios";

/**
 * The backend's `/compare/` endpoint is currently a literal stub
 * (`{"comparison": "not implemented yet"}`) and its eventual real shape
 * isn't finalized server-side (comparison_service returns a raw Groq
 * text string, not structured JSON). ComparePage drives its metrics
 * table from two `getInvestigationDetail()` calls instead, and only
 * uses this for the free-text AI summary panel, tolerating the stub.
 */
export async function compareInvestigations(id1, id2) {
  const { data } = await apiClient.get("/compare/", { params: { id1, id2 } });
  return data;
}
