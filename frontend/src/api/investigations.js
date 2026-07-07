import { apiClient } from "../lib/axios";

export async function listInvestigations() {
  const { data } = await apiClient.get("/investigations/");
  return data;
}

/**
 * Returns the full analysis result once REASON has run: company,
 * financials, risk_analysis (with red_flags), executive_summary,
 * recommendations, health_subscores. Fields are still optional/absent
 * for investigations that haven't finished analysis yet -- every
 * consuming component reads them defensively.
 */
export async function getInvestigationDetail(id) {
  const { data } = await apiClient.get(`/investigations/${id}`);
  return data;
}

export async function getInvestigationStatus(id) {
  const { data } = await apiClient.get(`/investigations/${id}/status`);
  return data;
}

/** Every source the GATHER stage actually fetched content from, so a
 * user can follow the same trail the AI used. */
export async function getInvestigationSources(id) {
  const { data } = await apiClient.get(`/investigations/${id}/sources`);
  return data;
}
