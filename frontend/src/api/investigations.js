import { apiClient } from "../lib/axios";

export async function listInvestigations() {
  const { data } = await apiClient.get("/investigations/");
  return data;
}

/**
 * `GET /investigations/{id}` today returns only the flat `InvestigationOut`
 * shape (id, company_name, status, health_score, risk_score, source_type,
 * created_at) — the backend hasn't wired up persistence of the nested
 * analysis result yet (company overview, yearly financials, risk
 * breakdown, executive summary, recommendations all get computed but
 * never saved). Once that lands, those keys will simply appear on this
 * same object. Every component that reads `investigation.company`,
 * `investigation.financials`, `investigation.risk_analysis`,
 * `investigation.executive_summary`, `investigation.recommendations`
 * already does so optionally, so no frontend change is required then.
 */
export async function getInvestigationDetail(id) {
  const { data } = await apiClient.get(`/investigations/${id}`);
  return data;
}

export async function getInvestigationStatus(id) {
  const { data } = await apiClient.get(`/investigations/${id}/status`);
  return data;
}
