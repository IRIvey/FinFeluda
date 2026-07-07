import { apiClient } from "../lib/axios";

/**
 * Re-runs the REASON stage from the chunks already stored in Qdrant
 * during `/upload/` — no re-upload needed. The backend allows this for
 * gathered, completed, and failed investigations, so it's the retry
 * path after a transient analysis failure (e.g. an LLM rate limit).
 */
export async function triggerAnalyze(investigationId) {
  const { data } = await apiClient.post(`/analyze/${investigationId}`);
  return data;
}
