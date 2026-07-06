import { useParams } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Sidebar } from "../components/layout/Sidebar";
import { ChatWindow } from "../components/chat/ChatWindow";
import { ChatInput } from "../components/chat/ChatInput";
import { useInvestigation } from "../hooks/useInvestigation";
import { useChat } from "../hooks/useChat";

export function ChatPage() {
  const { id } = useParams();
  const { data: investigation } = useInvestigation(id);
  const { messages, sendMessage, isSending } = useChat(id);

  return (
    <PageWrapper>
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">Ask AI</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">
          {investigation?.company_name || "This investigation"}
        </h1>
      </div>

      <div className="flex gap-8">
        <Sidebar investigationId={id} companyName={investigation?.company_name} />

        <div className="glass-card flex min-w-0 flex-1 flex-col" style={{ height: "65vh" }}>
          <ChatWindow messages={messages} />
          <ChatInput onSend={sendMessage} isSending={isSending} />
        </div>
      </div>
    </PageWrapper>
  );
}
