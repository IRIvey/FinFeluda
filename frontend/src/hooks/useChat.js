import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendChatMessage } from "../api/chat";

export function useChat(investigationId) {
  const [messages, setMessages] = useState([]);

  const mutation = useMutation({
    mutationFn: (question) => sendChatMessage({ investigationId, question }),
  });

  const sendMessage = async (question) => {
    const trimmed = question.trim();
    if (!trimmed) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);

    try {
      const response = await mutation.mutateAsync(trimmed);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, sources: response.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: err.message, isError: true },
      ]);
    }
  };

  return { messages, sendMessage, isSending: mutation.isPending };
}
