import { apiClient } from "../lib/axios";

export async function sendChatMessage({ investigationId, question }) {
  const { data } = await apiClient.post("/chat/", {
    investigation_id: investigationId,
    question,
  });
  return data;
}

export async function getChatHistory(investigationId) {
  const { data } = await apiClient.get(`/chat/${investigationId}`);
  return data;
}
