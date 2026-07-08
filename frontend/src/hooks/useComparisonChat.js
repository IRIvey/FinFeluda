import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { sendComparisonChatMessage, getComparisonChatHistory } from "../api/compare";

/** Mirrors useChat, but scoped to a pair of investigation IDs instead
 * of one -- only active once both Company A and Company B are picked
 * on the Compare page. */
export function useComparisonChat(investigationIdA, investigationIdB) {
  const [messages, setMessages] = useState([]);
  const [historySeeded, setHistorySeeded] = useState(false);
  const bothSelected = Boolean(investigationIdA && investigationIdB);

  const historyQuery = useQuery({
    queryKey: ["comparison-chat-history", investigationIdA, investigationIdB],
    queryFn: () => getComparisonChatHistory(investigationIdA, investigationIdB),
    enabled: bothSelected,
  });

  useEffect(() => {
    // Swapping either company starts a fresh thread client-side too --
    // matches the backend treating a different (A, B) pair as a
    // different conversation.
    setMessages([]);
    setHistorySeeded(false);
  }, [investigationIdA, investigationIdB]);

  useEffect(() => {
    if (historyQuery.data && !historySeeded) {
      setMessages(historyQuery.data);
      setHistorySeeded(true);
    }
  }, [historyQuery.data, historySeeded]);

  const mutation = useMutation({
    mutationFn: (question) =>
      sendComparisonChatMessage({ investigationIdA, investigationIdB, question }),
  });

  const sendMessage = async (question) => {
    const trimmed = question.trim();
    if (!trimmed || !bothSelected) return;

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
    isHistoryLoading: bothSelected && historyQuery.isLoading,
    bothSelected,
  };
}
