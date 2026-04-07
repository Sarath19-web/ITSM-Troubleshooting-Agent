export interface KBSource {
  category: string;
  preview: string;
}

export interface Ticket {
  ticket_id: string;
  status: "Open" | "In Progress" | "Resolved" | "Closed";
  priority: "P1" | "P2" | "P3" | "P4";
  priority_label: string;
  category: string;
  assigned_to: string;
  summary: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  notes?: string[];
  troubleshooting_steps?: string[];
  conversation_summary?: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  intent: string;
  category: string;
  troubleshoot_turn: number;
  max_turns: number;
  ticket: Ticket | null;
  response_time_ms: number;
  kb_sources: KBSource[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: Date;
  ticket?: Ticket;
  kb_sources?: KBSource[];
  troubleshoot_turn?: number;
  max_turns?: number;
}

export interface TicketStats {
  open: number;
  in_progress: number;
  resolved: number;
  total: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface Session {
  id: string;
  label: string;
  messageCount: number;
  lastMessage?: string;
}
