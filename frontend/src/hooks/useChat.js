import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { sendChatMessage, getChatHistory } from "../api/chat";

export function useChat(investigationId) {
  const [messages, setMessages] = useState([]);
  const [historySeeded, setHistorySeeded] = useState(false);

  // Loads whatever was already said in this investigation's chat, so
  // reopening it later shows the full past conversation instead of a
  // blank window -- same idea as reopening a Claude/ChatGPT thread.
  const historyQuery = useQuery({
    queryKey: ["chat-history", investigationId],
    queryFn: () => getChatHistory(investigationId),
    enabled: Boolean(investigationId),
  });

  useEffect(() => {
    // Seed local state from the server once per investigation. Only
    // seeding once (not on every refetch) keeps messages sent earlier
    // in this same session from being clobbered/duplicated.
    setMessages([]);
    setHistorySeeded(false);
  }, [investigationId]);

  useEffect(() => {
    if (historyQuery.data && !historySeeded) {
      setMessages(historyQuery.data);
      setHistorySeeded(true);
    }
  }, [historyQuery.data, historySeeded]);

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

  return {
    messages,
    sendMessage,
    isSending: mutation.isPending,
    isHistoryLoading: historyQuery.isLoading,
  };
}
