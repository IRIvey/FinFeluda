import { apiClient } from "../lib/axios";

/**
 * Kept for parity with the backend router, but NOT called anywhere in
 * the normal upload -> processing -> dashboard flow: `/analyze/{id}`
 * requires `pdf_paths`, which are server-side temp file paths created
 * during `/upload/` and never returned to the browser. Calling this
 * from the frontend can't correctly include uploaded PDF content.
 */
export async function triggerAnalyze(investigationId, { companyName, websiteUrl } = {}) {
  const { data } = await apiClient.post(`/analyze/${investigationId}`, null, {
    params: { company_name: companyName, website_url: websiteUrl },
  });
  return data;
}
