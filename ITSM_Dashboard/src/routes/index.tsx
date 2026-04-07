import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sendMessage, resetSession, createTicket, getCategories, getSessionHistory } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import type { ChatMessage as ChatMessageType } from "@/lib/types";
import { ChatMessage, TypingIndicator } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { CreateTicketModal } from "@/components/chat/CreateTicketModal";
import { AppSidebar } from "@/components/AppSidebar";
import { Bot } from "lucide-react";

export const Route = createFileRoute("/")({
  component: ChatPage,
  validateSearch: (search: Record<string, unknown>) => ({
    sessionId: search.sessionId as string | undefined,
  }),
});

function ChatPage() {
  const { sessionId: urlSessionId } = Route.useSearch();
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(() => urlSessionId || `session-${Date.now()}`);
  const [modalOpen, setModalOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });

  // Load session history when sessionId changes
  useEffect(() => {
    const loadSessionHistory = async () => {
      if (urlSessionId) {
        try {
          const result = await getSessionHistory(urlSessionId);
          const mappedMessages: ChatMessageType[] = result.history.map((msg, idx) => ({
            id: `msg-${idx}`,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
          }));
          setMessages(mappedMessages);
          setSessionId(urlSessionId);
        } catch (error) {
          console.error("Failed to load session history:", error);
          setMessages([]);
        }
      }
    };
    loadSessionHistory();
  }, [urlSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: ChatMessageType = { id: `u-${Date.now()}`, role: "user", content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const res = await sendMessage({ message: text, session_id: sessionId, user_name: "User" });
      const agentMsg: ChatMessageType = {
        id: `a-${Date.now()}`,
        role: "agent",
        content: res.reply,
        timestamp: new Date(),
        ticket: res.ticket || undefined,
        kb_sources: res.kb_sources,
        troubleshoot_turn: res.troubleshoot_turn,
        max_turns: res.max_turns,
        from_cache: res.from_cache,
        cache_type: res.cache_type,
      };
      setMessages((prev) => [...prev, agentMsg]);
      if (res.ticket) {
        queryClient.invalidateQueries({ queryKey: ["tickets"] });
        queryClient.invalidateQueries({ queryKey: ["ticket-stats"] });
      }
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    } catch {
      setMessages((prev) => [...prev, { id: `e-${Date.now()}`, role: "agent", content: "⚠️ Cannot reach the IT agent server. Please check the backend is running and try again.", timestamp: new Date() }]);
    } finally {
      setIsTyping(false);
    }
  }, [sessionId, queryClient]);

  const handleNewChat = useCallback(async () => {
    try {
      const newId = `session-${Date.now()}`;
      await resetSession(newId);
      setSessionId(newId);
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    } catch {
      const newId = `session-${Date.now()}`;
      setSessionId(newId);
      setMessages([]);
    }
  }, [queryClient]);

  const handleCreateTicket = useCallback(async (data: { summary: string; category: string; priority: string; description: string }) => {
    try {
      const result = await createTicket({ ...data, session_id: sessionId, user_name: "User" });
      const ticket = result.ticket || result as any;
      setMessages((prev) => [...prev, {
        id: `t-${Date.now()}`,
        role: "agent",
        content: `Support ticket created successfully.`,
        timestamp: new Date(),
        ticket,
      }]);
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["ticket-stats"] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    } catch {
      setMessages((prev) => [...prev, { id: `e-${Date.now()}`, role: "agent", content: "⚠️ Failed to create ticket. Please try again.", timestamp: new Date() }]);
    }
  }, [sessionId, queryClient]);

  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar />
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
            {messages.length === 0 && !isTyping && (
              <div className="text-center py-20">
                <Bot className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                <p className="text-muted-foreground">Start a conversation with the IT Helpdesk Assistant</p>
              </div>
            )}
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

        <CreateTicketModal open={modalOpen} onClose={() => setModalOpen(false)} onSubmit={handleCreateTicket} categories={categories} />
      </main>
    </div>
  );
}
