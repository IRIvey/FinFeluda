import { apiClient } from "../lib/axios";

export async function getReport(investigationId) {
  const { data } = await apiClient.get(`/report/${investigationId}`);
  return data;
}

export async function downloadReportUrl(investigationId) {
  const { data } = await apiClient.get(`/report/${investigationId}/download`);
  return data;
}
