import { apiClient } from "../lib/axios";

export async function getReport(investigationId) {
  const { data } = await apiClient.get(`/report/${investigationId}`);
  return data;
}

/**
 * The backend streams the PDF bytes directly (Cloudinary is archival
 * only — its public raw-file URLs 401 on default account settings, so
 * they must never be the download path). Returns a Blob.
 */
export async function downloadReportPdf(investigationId) {
  const { data } = await apiClient.get(`/report/${investigationId}/download`, {
    responseType: "blob",
  });
  return data;
}
