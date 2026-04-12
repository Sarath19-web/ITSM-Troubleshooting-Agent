import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sendMessage, resetSession, createTicket, getCategories, getSessionHistory, getTicket } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import type { ChatMessage as ChatMessageType, Ticket } from "@/lib/types";
import { ChatMessage, TypingIndicator } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { CreateTicketModal } from "@/components/chat/CreateTicketModal";
import { AppSidebar } from "@/components/AppSidebar";
import { Bot } from "lucide-react";
import { useSessionWS } from "@/hooks/use-session-ws";

export const Route = createFileRoute("/")({
  component: ChatPage,
  validateSearch: (search: Record<string, unknown>) => ({
    sessionId: search.sessionId as string | undefined,
  }),
});

function ChatPage() {
  const { sessionId: urlSessionId } = Route.useSearch();
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessageType[]>(() => {
    // Show greeting on initial load if no session to restore
    if (!urlSessionId) {
      return [{
        id: `greeting-${Date.now()}`,
        role: "agent" as const,
        content: "Hi there! I'm Alex, your IT Helpdesk Assistant \ud83d\udc4b\n\nI can help you troubleshoot technical issues \u2014 VPN, email, password, printer, software, and more. Or I can create a support ticket for you.\n\n**What\u2019s going on today?**",
        timestamp: new Date(),
      }];
    }
    return [];
  });
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(() => urlSessionId || `session-${Date.now()}`);
  const [modalOpen, setModalOpen] = useState(false);
  const [trackedTickets, setTrackedTickets] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);

  // Real-time: receive messages pushed by IT Support agent via WebSocket
  useSessionWS(sessionId, useCallback((evt) => {
    if (evt.type !== "new_message") return;
    const m = evt.message;
    // Only show human-agent messages (AI replies are already added via handleSend)
    if (m.metadata?.intent !== "human_agent") return;
    setMessages((prev) => [...prev, {
      id: `ws-${Date.now()}-${Math.random()}`,
      role: m.role as "user" | "agent",
      content: m.content,
      timestamp: new Date(m.timestamp),
      metadata: {
        intent: "human_agent",
        agent_name: (m.metadata as any)?.agent_name || "IT Support",
      },
    }]);
  }, []));

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
          const mappedMessages: ChatMessageType[] = await Promise.all(
            result.history.map(async (msg, idx) => {
              let content = msg.content;
              let ticket = undefined;

              // If message has ticket_created metadata, fetch the ticket and strip markdown
              const ticketId = msg.metadata?.ticket_created;
              if (ticketId) {
                try {
                  ticket = await getTicket(ticketId);
                  // Strip the markdown ticket card from content
                  content = content.replace(/\n*---\n*###\s*✅\s*Ticket Created[\s\S]*$/, "").trim();
                } catch {
                  // Ticket fetch failed, keep original content
                }
              }

              return {
                id: `msg-${idx}`,
                role: msg.role,
                content,
                timestamp: new Date(msg.timestamp),
                ticket,
                from_cache: msg.metadata?.from_cache,
                cache_type: msg.metadata?.cache_type,
                metadata: msg.metadata ? {
                  intent: msg.metadata.intent,
                  agent_name: (msg.metadata as any).agent_name,
                } : undefined,
              } as ChatMessageType;
            })
          );
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

  // Poll for ticket status updates
  useEffect(() => {
    if (trackedTickets.size === 0) return;

    const pollTickets = async () => {
      for (const ticketId of trackedTickets) {
        try {
          const ticket = await getTicket(ticketId);
          
          // Check if ticket status changed to Resolved or Closed
          if (ticket.status === "Resolved" || ticket.status === "Closed") {
            // Add resolution message to chat
            setMessages((prev) => {
              // Check if we already added a resolution message for this ticket
              const hasResolution = prev.some(msg => 
                msg.content.includes(`ticket ${ticketId}`) && 
                (msg.content.includes("resolved") || msg.content.includes("closed"))
              );
              if (hasResolution) return prev;
              
              return [...prev, {
                id: `ticket-resolved-${ticketId}-${Date.now()}`,
                role: "agent",
                content: `✓ **Ticket ${ticketId} has been ${ticket.status.toLowerCase()}**`,
                timestamp: new Date(),
              }];
            });
            
            // Stop tracking this ticket
            setTrackedTickets(prev => {
              const updated = new Set(prev);
              updated.delete(ticketId);
              return updated;
            });
          }
        } catch (error) {
          console.error(`Failed to poll ticket ${ticketId}:`, error);
        }
      }
    };

    const interval = setInterval(pollTickets, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [trackedTickets]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: ChatMessageType = { id: `u-${Date.now()}`, role: "user", content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const res = await sendMessage({ message: text, session_id: sessionId, user_name: "User" });
      if (!res.reply && res.agent_paused) {
        return;
      }
      const agentMsg: ChatMessageType = {
        id: `a-${Date.now()}`,
        role: "agent",
        content: res.reply,
        timestamp: new Date(),
        ticket: res.ticket || undefined,
        draft_ticket: res.draft_ticket || undefined,
        kb_sources: res.kb_sources,
        troubleshoot_turn: res.troubleshoot_turn,
        max_turns: res.max_turns,
        from_cache: res.from_cache,
        cache_type: res.cache_type,
      };
      setMessages((prev) => [...prev, agentMsg]);
      
      // Track ticket if one was created in this response
      if (res.ticket) {
        setTrackedTickets(prev => new Set([...prev, res.ticket!.ticket_id]));
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
      setMessages([{
        id: `greeting-${Date.now()}`,
        role: "agent" as const,
        content: "Hi there! I'm Alex, your IT Helpdesk Assistant \ud83d\udc4b\n\nI can help you troubleshoot technical issues \u2014 VPN, email, password, printer, software, and more. Or I can create a support ticket for you.\n\n**What\u2019s going on today?**",
        timestamp: new Date(),
      }]);
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    } catch {
      const newId = `session-${Date.now()}`;
      setSessionId(newId);
      setMessages([{
        id: `greeting-${Date.now()}`,
        role: "agent" as const,
        content: "Hi there! I'm Alex, your IT Helpdesk Assistant \ud83d\udc4b\n\nI can help you troubleshoot technical issues \u2014 VPN, email, password, printer, software, and more. Or I can create a support ticket for you.\n\n**What\u2019s going on today?**",
        timestamp: new Date(),
      }]);
    }
  }, [queryClient]);

  const handleCreateTicket = useCallback(async (data: { summary: string; category: string; priority: string; description: string }) => {
    try {
      const result = await createTicket({ ...data, session_id: sessionId, user_name: "User" });
      const ticket = result.ticket || result as any;
      
      // Track this ticket for status updates
      setTrackedTickets(prev => new Set([...prev, ticket.ticket_id]));
      
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

  const handleDraftSubmit = useCallback(async (edited: Partial<Ticket>) => {
    try {
      const result = await createTicket({
        summary: edited.summary || "Support Ticket",
        category: edited.category || "Other",
        priority: edited.priority || "P3",
        description: edited.description || "",
        session_id: sessionId,
        user_name: "User",
      });
      const ticket = result.ticket || result as any;

      // Track this ticket for status updates
      setTrackedTickets(prev => new Set([...prev, ticket.ticket_id]));

      // Remove draft from messages and add confirmed ticket message
      setMessages(prev => {
        const updated = prev.map(msg =>
          msg.draft_ticket ? { ...msg, draft_ticket: undefined } : msg
        );
        return [...updated, {
          id: `t-${Date.now()}`,
          role: "agent" as const,
          content: "Your ticket has been submitted successfully! 🎉",
          timestamp: new Date(),
          ticket,
        }];
      });

      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["ticket-stats"] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    } catch {
      setMessages(prev => [...prev, {
        id: `e-${Date.now()}`,
        role: "agent" as const,
        content: "⚠️ Failed to create ticket. Please try again.",
        timestamp: new Date(),
      }]);
    }
  }, [sessionId, queryClient]);

  const handleDraftCancel = useCallback(async () => {
    // Send 'no' to backend to clear draft state
    try {
      await sendMessage({ message: "no", session_id: sessionId, user_name: "User" });
    } catch { /* swallow */ }

    // Remove draft from UI
    setMessages(prev =>
      prev.map(msg =>
        msg.draft_ticket ? { ...msg, draft_ticket: undefined, content: msg.content + "\n\n*Ticket draft cancelled.*" } : msg
      )
    );
  }, [sessionId]);

  return (
    <div className="flex min-h-screen w-full">
      <div className="hidden md:block">
        <AppSidebar />
      </div>
      <main className="flex-1 flex flex-col h-screen">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 md:px-6 py-3 md:py-4 border-b border-border bg-card">
          <div className="w-8 h-8 md:w-9 md:h-9 rounded-full bg-primary flex items-center justify-center shrink-0">
            <Bot className="w-4 h-4 md:w-5 md:h-5 text-primary-foreground" />
          </div>
          <div className="min-w-0">
            <h1 className="text-sm font-semibold truncate">Alex — IT Helpdesk Assistant</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-success" />
              <span className="text-xs text-muted-foreground">Online</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 md:px-4 py-4 md:py-6">
          <div className="max-w-[800px] mx-auto">
            {messages.length === 0 && !isTyping && (
              <div className="text-center py-20">
                <Bot className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                <p className="text-muted-foreground">Start a conversation with the IT Helpdesk Assistant</p>
              </div>
            )}
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onSubmitDraft={handleDraftSubmit}
                onCancelDraft={handleDraftCancel}
              />
            ))}
            {isTyping && <TypingIndicator />}
          </div>
        </div>

        {/* Input */}
        <div className="max-w-[800px] mx-auto w-full px-2 md:px-0">
          <ChatInput onSend={handleSend} onNewChat={handleNewChat} onCreateTicket={() => setModalOpen(true)} disabled={isTyping} />
        </div>

        <CreateTicketModal open={modalOpen} onClose={() => setModalOpen(false)} onSubmit={handleCreateTicket} categories={categories} />
      </main>
    </div>
  );
}
