import type {
  ChatResponse,
  Ticket,
  TicketStats,
  CacheStats,
  FAQ,
  PipelineEvent,
  SessionSummary,
  SessionDetail,
  Message,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

// Health
export interface HealthResponse {
  status: string;
  kb_loaded: boolean;
  model: string;
  version: string;
}
export const getHealth = () => request<HealthResponse>("/health");

// Categories
export const getCategories = () => request<string[]>("/categories");

// Chat
export const sendMessage = (body: { message: string; session_id: string; user_name?: string }) =>
  request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify(body) });

// Tickets
export interface TicketFilters {
  status?: string;
  priority?: string;
  category?: string;
}
export const listTickets = async (filters?: TicketFilters): Promise<Ticket[]> => {
  const qs = new URLSearchParams();
  if (filters?.status) qs.set("status", filters.status);
  if (filters?.priority) qs.set("priority", filters.priority);
  if (filters?.category) qs.set("category", filters.category);
  const result = await request<{ tickets: Ticket[]; count: number } | Ticket[]>(`/tickets?${qs}`);
  if (Array.isArray(result)) return result;
  return result.tickets;
};
export const getTicket = (id: string) => request<Ticket>(`/tickets/${id}`);
export const createTicket = (body: {
  session_id: string;
  summary: string;
  category: string;
  priority: string;
  description: string;
  user_name: string;
}) => request<{ status: string; ticket: Ticket }>("/tickets", { method: "POST", body: JSON.stringify(body) });
export const updateTicket = (id: string, body: Partial<Ticket>) =>
  request<{ status: string; ticket: Ticket }>(`/tickets/${id}`, { method: "PATCH", body: JSON.stringify(body) });
export const getTicketStats = () => request<TicketStats>("/tickets/stats");

// Agent assist — human IT staff sends a reply into a session
export const agentReply = (body: { session_id: string; message: string; agent_name?: string }) =>
  request<{ status: string; session_id: string; message_count: number }>("/agent/reply", { method: "POST", body: JSON.stringify(body) });

// Agent pause/resume — toggle AI agent for a session
export const pauseAgent = (sessionId: string) =>
  request<{ status: string; session_id: string }>(`/agent/pause/${sessionId}`, { method: "POST" });
export const resumeAgent = (sessionId: string) =>
  request<{ status: string; session_id: string }>(`/agent/resume/${sessionId}`, { method: "POST" });
export const getAgentStatus = (sessionId: string) =>
  request<{ session_id: string; paused: boolean }>(`/agent/status/${sessionId}`);

// Sessions
export const listSessions = (limit = 50) =>
  request<{ sessions: SessionSummary[] }>(`/sessions?limit=${limit}`);
export const getSession = (id: string) => request<SessionDetail>(`/session/${id}`);
export const getSessionHistory = (id: string) =>
  request<{ session_id: string; history: Message[] }>(`/session/${id}/history`);
export const resetSession = (id: string) =>
  request<{ status: string; session_id: string }>("/session/reset", { method: "POST", body: JSON.stringify({ session_id: id }) });
export const deleteSession = (id: string) =>
  request<{ status: string }>(`/session/${id}`, { method: "DELETE" });

// Cache
export const getCacheStats = () => request<CacheStats>("/cache/stats");
export const getTrendingFaqs = () => request<{ trending_faqs: FAQ[] }>("/cache/trending");
export const clearCache = () => request<{ status: string }>("/cache", { method: "DELETE" });

// Logs
export interface AccessLogEntry {
  timestamp: string;
  method: string;
  path: string;
  status_code: number;
  duration_ms: number;
}
export interface ErrorLogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  module?: string;
  function?: string;
  line?: number;
  exception?: string;
  session_id?: string;
}
export const getPipelineLogs = (limit = 100, sessionId?: string) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (sessionId) qs.set("session_id", sessionId);
  return request<{ events: PipelineEvent[]; count: number }>(`/logs/pipeline?${qs}`);
};
export const getAccessLogs = (limit = 100) =>
  request<{ requests: AccessLogEntry[]; count: number }>(`/logs/access?limit=${limit}`);
export const getErrorLogs = (limit = 100) =>
  request<{ errors: ErrorLogEntry[]; count: number }>(`/logs/errors?limit=${limit}`);
