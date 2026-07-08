import { apiClient } from "../lib/axios";

export async function uploadInvestigation({ companyName, files = [], websiteUrl }) {
  const formData = new FormData();
  formData.append("company_name", companyName);
  formData.append("website_url", websiteUrl);
  for (const file of files) {
    formData.append("files", file);
  }

  const { data } = await apiClient.post("/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
