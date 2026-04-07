import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect, useCallback } from "react";
import { useApi } from "@/lib/api-context";
import type { ChatMessage as ChatMessageType, Session } from "@/lib/types";
import { ChatMessage, TypingIndicator } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { CreateTicketModal } from "@/components/chat/CreateTicketModal";
import { AppSidebar } from "@/components/AppSidebar";
import { Bot } from "lucide-react";

export const Route = createFileRoute("/")({
  component: ChatPage,
});

function ChatPage() {
  const api = useApi();
  const [messages, setMessages] = useState<ChatMessageType[]>(() => [
    {
      id: "welcome",
      role: "agent",
      content: "Hi! I'm Alex, your IT Helpdesk Assistant.\n\nI can help you troubleshoot technical issues, create support tickets, or check the status of existing tickets.\n\nWhat can I help you with today?",
      timestamp: new Date(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState("session-default");
  const [modalOpen, setModalOpen] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([
    { id: "s1", label: "VPN Issue", messageCount: 3 },
    { id: "s2", label: "Outlook crash", messageCount: 5 },
    { id: "s3", label: "Password reset", messageCount: 2 },
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: ChatMessageType = { id: `u-${Date.now()}`, role: "user", content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const res = await api.sendMessage(text, sessionId, "John Doe");
      const agentMsg: ChatMessageType = {
        id: `a-${Date.now()}`,
        role: "agent",
        content: res.reply,
        timestamp: new Date(),
        ticket: res.ticket || undefined,
        kb_sources: res.kb_sources,
        troubleshoot_turn: res.troubleshoot_turn,
        max_turns: res.max_turns,
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch {
      setMessages((prev) => [...prev, { id: `e-${Date.now()}`, role: "agent", content: "I'm having trouble connecting to the server. Please try again in a moment.", timestamp: new Date() }]);
    } finally {
      setIsTyping(false);
    }
  }, [api, sessionId]);

  const handleNewChat = useCallback(async () => {
    const res = await api.resetSession();
    setSessionId(res.session_id);
    setMessages([
      { id: "welcome-new", role: "agent", content: "Hi! I'm Alex, your IT Helpdesk Assistant.\n\nHow can I help you today?", timestamp: new Date() },
    ]);
  }, [api]);

  const handleCreateTicket = useCallback(async (data: { summary: string; category: string; priority: string; description: string }) => {
    const ticket = await api.createTicket({ ...data, session_id: sessionId, user_name: "John Doe" });
    setMessages((prev) => [...prev, {
      id: `t-${Date.now()}`,
      role: "agent",
      content: `I've created a support ticket for you.`,
      timestamp: new Date(),
      ticket,
    }]);
  }, [api, sessionId]);

  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar sessions={sessions} openTickets={4} avgResponseTime="4.2s" baseUrl={api.baseUrl} onBaseUrlChange={api.setBaseUrl} />
      <main className="flex-1 flex flex-col h-screen">
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border bg-card">
          <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center">
            <Bot className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-semibold">Alex — IT Helpdesk Assistant</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-success" />
              <span className="text-xs text-muted-foreground">Online</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-[800px] mx-auto">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isTyping && <TypingIndicator />}
          </div>
        </div>

        {/* Input */}
        <div className="max-w-[800px] mx-auto w-full">
          <ChatInput onSend={handleSend} onNewChat={handleNewChat} onCreateTicket={() => setModalOpen(true)} disabled={isTyping} />
        </div>

        <CreateTicketModal open={modalOpen} onClose={() => setModalOpen(false)} onSubmit={handleCreateTicket} />
      </main>
    </div>
  );
}
