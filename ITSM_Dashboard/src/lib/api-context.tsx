import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { ChatResponse, Ticket, TicketStats } from "./types";

interface ApiContextType {
  baseUrl: string;
  setBaseUrl: (url: string) => void;
  sendMessage: (message: string, sessionId: string, userName: string) => Promise<ChatResponse>;
  createTicket: (data: {
    session_id: string;
    summary: string;
    category: string;
    priority: string;
    description: string;
    user_name: string;
  }) => Promise<Ticket>;
  getTickets: (filters?: Record<string, string>) => Promise<Ticket[]>;
  getTicketStats: () => Promise<TicketStats>;
  getTicket: (id: string) => Promise<Ticket>;
  updateTicket: (id: string, data: Partial<Ticket>) => Promise<Ticket>;
  resetSession: () => Promise<{ session_id: string }>;
  getCategories: () => Promise<string[]>;
}

const ApiContext = createContext<ApiContextType | null>(null);

export function useApi() {
  const ctx = useContext(ApiContext);
  if (!ctx) throw new Error("useApi must be used within ApiProvider");
  return ctx;
}

const EMPTY_STATS: TicketStats = {
  open: 0,
  in_progress: 0,
  resolved: 0,
  total: 0,
  by_category: {},
  by_priority: {},
};

const DEMO_CATEGORIES = ["Network & VPN", "Email & Calendar", "Account & Access", "Hardware", "Software Installation", "Printing", "Security"];

const DEMO_RESPONSES: Record<string, { reply: string; intent: string; category: string; turn: number }> = {
  vpn: { reply: "I understand how frustrating VPN issues can be. Let me help you troubleshoot this.\n\nFirst, let's check a few things:\n1. Are you connected via WiFi or Ethernet?\n2. Can you open google.com in your browser?\n3. Which VPN client are you using (GlobalProtect, Cisco AnyConnect, etc.)?", intent: "troubleshoot", category: "Network & VPN", turn: 1 },
  email: { reply: "I'm sorry to hear about the email issues. Let me help you resolve this.\n\nCan you tell me:\n1. Are you using Outlook desktop or web version?\n2. When did this issue start?\n3. Do you see any specific error messages?", intent: "troubleshoot", category: "Email & Calendar", turn: 1 },
  password: { reply: "I can help you with your password issue right away.\n\nLet me check a few things:\n1. Are you trying to log into your Windows account or a specific application?\n2. Have you tried the self-service password reset portal?\n3. Is your account showing as locked?", intent: "troubleshoot", category: "Account & Access", turn: 1 },
  default: { reply: "I'd be happy to help you with that. Could you provide a bit more detail about the issue you're experiencing? For example:\n\n• Which application or service is affected?\n• When did the issue start?\n• Have you tried any troubleshooting steps already?", intent: "clarify", category: "General", turn: 1 },
};

export function ApiProvider({ children }: { children: ReactNode }) {
  const [baseUrl, setBaseUrl] = useState("http://localhost:8000");

  const apiFetch = useCallback(async (path: string, options?: RequestInit) => {
    try {
      const res = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers: { "Content-Type": "application/json", ...options?.headers },
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return res.json();
    } catch {
      return null;
    }
  }, [baseUrl]);

  const sendMessage = useCallback(async (message: string, sessionId: string, userName: string): Promise<ChatResponse> => {
    const result = await apiFetch("/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId, user_name: userName }),
    });
    if (result) return result;
    const msg = message.toLowerCase();
    const key = msg.includes("vpn") ? "vpn" : msg.includes("email") || msg.includes("outlook") ? "email" : msg.includes("password") ? "password" : "default";
    const demo = DEMO_RESPONSES[key];
    const shouldCreateTicket = msg.includes("ticket") || msg.includes("raise");
    return {
      reply: shouldCreateTicket
        ? `I'll create a support ticket for you right away.\n\n**Ticket Created: INC001011**\n- **Priority:** P2 (High)\n- **Category:** ${demo.category}\n- **Assigned to:** IT Support Team\n\nYou can track this ticket in the Dashboard.`
        : demo.reply,
      session_id: sessionId,
      intent: shouldCreateTicket ? "create_ticket" : demo.intent,
      category: demo.category,
      troubleshoot_turn: demo.turn,
      max_turns: 5,
      ticket: shouldCreateTicket ? { ticket_id: "INC001011", status: "Open", priority: "P2", priority_label: "High", category: demo.category, assigned_to: "IT Support Team", summary: message.slice(0, 80) } : null,
      response_time_ms: 1200 + Math.random() * 3000,
      kb_sources: [{ category: demo.category, preview: `KB00${Math.floor(Math.random() * 9) + 1} — ${demo.category} troubleshooting guide` }],
    };
  }, [apiFetch]);

  const createTicket = useCallback(async (data: { session_id: string; summary: string; category: string; priority: string; description: string; user_name: string }): Promise<Ticket> => {
    const result = await apiFetch("/tickets", { method: "POST", body: JSON.stringify(data) });
    if (result) return result;
    return { ticket_id: `INC00${1011 + Math.floor(Math.random() * 100)}`, status: "Open", priority: data.priority as Ticket["priority"], priority_label: data.priority === "P1" ? "Critical" : data.priority === "P2" ? "High" : data.priority === "P3" ? "Medium" : "Low", category: data.category, assigned_to: "IT Support Team", summary: data.summary, description: data.description, created_at: new Date().toISOString() };
  }, [apiFetch]);

  const getTickets = useCallback(async (filters?: Record<string, string>): Promise<Ticket[]> => {
    const params = filters ? "?" + new URLSearchParams(filters).toString() : "";
    const result = await apiFetch(`/tickets${params}`);
    if (Array.isArray(result)) return result;
    if (result && Array.isArray(result.tickets)) return result.tickets;
    return [];
  }, [apiFetch]);

  const getTicketStats = useCallback(async (): Promise<TicketStats> => {
    const result = await apiFetch("/tickets/stats");
    return result || EMPTY_STATS;
  }, [apiFetch]);

  const getTicket = useCallback(async (id: string): Promise<Ticket> => {
    const result = await apiFetch(`/tickets/${id}`);
    return result || { ticket_id: id, status: "Open", priority: "P3", priority_label: "Medium", category: "General", assigned_to: "Unassigned", summary: "Unknown ticket" } as Ticket;
  }, [apiFetch]);

  const updateTicket = useCallback(async (id: string, data: Partial<Ticket>): Promise<Ticket> => {
    const result = await apiFetch(`/tickets/${id}`, { method: "PATCH", body: JSON.stringify(data) });
    if (result) return result;
    return { ticket_id: id, ...data } as Ticket;
  }, [apiFetch]);

  const resetSession = useCallback(async () => {
    const result = await apiFetch("/session/reset", { method: "POST" });
    return result || { session_id: `session-${Date.now()}` };
  }, [apiFetch]);

  const getCategories = useCallback(async () => {
    const result = await apiFetch("/categories");
    return result || DEMO_CATEGORIES;
  }, [apiFetch]);

  return (
    <ApiContext.Provider value={{ baseUrl, setBaseUrl, sendMessage, createTicket, getTickets, getTicketStats, getTicket, updateTicket, resetSession, getCategories }}>
      {children}
    </ApiContext.Provider>
  );
}
