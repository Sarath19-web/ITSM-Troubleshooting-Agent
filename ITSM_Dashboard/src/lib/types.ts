export interface Message {
  role: "user" | "agent";
  content: string;
  timestamp: string;
  metadata?: {
    intent?: string;
    category?: string;
    turn?: number;
    from_cache?: boolean;
    cache_type?: "exact" | "semantic";
    kb_articles?: string[];
    ticket_created?: string;
  };
}

export interface KBSource {
  filename?: string;
  category: string;
  preview: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  intent: string | null;
  category: string | null;
  troubleshoot_turn: number;
  max_turns: number;
  deferred_intents?: string[];
  steps_completed?: string[];
  failed_steps?: string[];
  ticket: Ticket | null;
  draft_ticket?: Partial<Ticket> | null;
  response_time_ms: number;
  kb_sources: KBSource[];
  from_cache?: boolean;
  cache_type?: "exact" | "semantic";
}

export interface Ticket {
  ticket_id: string;
  number?: number;
  status: "Open" | "In Progress" | "Resolved" | "Closed";
  priority: "P1" | "P2" | "P3" | "P4";
  priority_label: string;
  category: string;
  summary: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  assigned_to: string;
  user_name?: string;
  session_id?: string | null;
  troubleshooting_steps_completed?: string[];
  conversation_summary?: string;
  notes?: Array<{ text: string; timestamp: string } | string>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: Date;
  ticket?: Ticket;
  draft_ticket?: Partial<Ticket>;
  kb_sources?: KBSource[];
  troubleshoot_turn?: number;
  max_turns?: number;
  from_cache?: boolean;
  cache_type?: "exact" | "semantic";
  metadata?: {
    intent?: string;
    agent_name?: string;
  };
}

export interface TicketStats {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  by_status?: Record<string, number>;
  by_priority?: Record<string, number>;
  by_category?: Record<string, number>;
}

export interface SessionSummary {
  session_id: string;
  user_name: string | null;
  label: string;
  category: string | null;
  message_count: number;
  ticket_created: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionDetail extends SessionSummary {
  troubleshoot_turn: number;
  max_turns: number;
  current_category: string | null;
  steps_completed: string[];
  failed_steps: string[];
  deferred_intents: string[];
  history: Message[];
  in_memory: boolean;
}

export interface CacheStats {
  total_entries: number;
  total_hits: number;
  max_size: number;
  similarity_threshold: number;
  trending_faqs: FAQ[];
}

export interface FAQ {
  question: string;
  category: string | null;
  hit_count: number;
  last_hit: string;
}

export interface PipelineEvent {
  timestamp: string;
  event_type: string;
  session_id: string | null;
  data: Record<string, unknown>;
}
