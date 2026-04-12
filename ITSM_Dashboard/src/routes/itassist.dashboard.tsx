import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import {
  Send, RefreshCw, Loader2, ChevronDown, ChevronUp,
  Headset, MessageSquare, Bot, User, ToggleLeft, ToggleRight,
  AlertTriangle, Clock, CheckCircle2, TrendingUp, Activity,
  FileText, Terminal, PanelLeftClose, PanelLeftOpen, Menu, X,
  MoreHorizontal, Wrench, ShieldCheck, RotateCcw, HelpCircle,
} from "lucide-react";
import {
  listTickets, updateTicket, getTicketStats, getSessionHistory,
  agentReply, pauseAgent, resumeAgent, getAgentStatus,
  getErrorLogs,
} from "@/lib/api";
import type { Ticket, Message } from "@/lib/types";
import { PriorityChip, StatusChip } from "@/components/shared/StatusChips";
import { Skeleton } from "@/components/ui/skeleton";
import { useSessionWS } from "@/hooks/use-session-ws";

export const Route = createFileRoute("/itassist/dashboard")({
  component: ITAssistPage,
});

// ─── KPI Card ─────────────────────────────────────────────────

function KPICard({
  label,
  value,
  icon: Icon,
  color,
  sub,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  sub?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-3 flex items-center gap-3 shadow-sm">
      <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center shrink-0`}>
        <Icon className="w-4 h-4 text-white" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
        <p className="text-lg font-bold text-foreground leading-tight">{value}</p>
      </div>
    </div>
  );
}

// ─── Mini bar for priority/category distribution ────────────────

function MiniDistribution({
  title,
  data,
  colors,
}: {
  title: string;
  data: Record<string, number>;
  colors: Record<string, string>;
}) {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  return (
    <div className="bg-card border border-border rounded-xl p-3 shadow-sm">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">{title}</p>
      <div className="w-full h-3 rounded-full bg-muted overflow-hidden flex">
        {Object.entries(data)
          .filter(([, v]) => v > 0)
          .map(([key, val]) => (
            <div
              key={key}
              className={`h-full ${colors[key] || "bg-gray-400"} transition-all`}
              style={{ width: `${(val / total) * 100}%` }}
              title={`${key}: ${val}`}
            />
          ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2.5">
        {Object.entries(data)
          .filter(([, v]) => v > 0)
          .map(([key, val]) => (
            <div key={key} className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${colors[key] || "bg-gray-400"}`} />
              <span className="text-xs text-muted-foreground">
                {key} <strong className="text-foreground">{val}</strong>
              </span>
            </div>
          ))}
      </div>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────

// ─── Ops Sidebar – error logs & pipeline activity ────────────

function OpsSidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const { data: errData } = useQuery({
    queryKey: ["error-logs"],
    queryFn: () => getErrorLogs(30),
    refetchInterval: 10_000,
  });

  const errorCount = errData?.errors?.length ?? 0;

  if (collapsed) {
    return (
      <div className="w-12 border-r border-border bg-card flex flex-col items-center py-3 gap-3 shrink-0">
        <button onClick={onToggle} className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors" title="Expand sidebar">
          <PanelLeftOpen className="w-4 h-4" />
        </button>
        <div className="w-6 h-px bg-border" />
        <Link to="/itassist/errors" className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors relative" title="Error Logs">
          <AlertTriangle className="w-4 h-4" />
          {errorCount > 0 && <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500" />}
        </Link>
        <Link to="/itassist/pipeline" className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors" title="Pipeline Logs">
          <Terminal className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="w-[200px] border-r border-border bg-card flex flex-col shrink-0 overflow-hidden">
      <div className="px-3 py-3 border-b border-border flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Operations</p>
        <button onClick={onToggle} className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-1">
        <Link
          to="/itassist/dashboard"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-accent text-foreground text-xs font-medium"
        >
          <Headset className="w-4 h-4" />
          <span>Dashboard</span>
        </Link>
        <Link
          to="/itassist/errors"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground text-xs font-medium transition-colors relative"
        >
          <AlertTriangle className="w-4 h-4" />
          <span className="flex-1">Error Logs</span>
          {errorCount > 0 && (
            <span className="text-[10px] bg-red-500/15 text-red-500 px-1.5 py-0.5 rounded-full font-bold">{errorCount}</span>
          )}
        </Link>
        <Link
          to="/itassist/pipeline"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground text-xs font-medium transition-colors"
        >
          <Terminal className="w-4 h-4" />
          <span>Pipeline Logs</span>
        </Link>
      </nav>
    </div>
  );
}

function ITAssistPage() {
  const queryClient = useQueryClient();
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobilePanel, setMobilePanel] = useState<"list" | "detail">("list");

  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets", { status: "" }],
    queryFn: () => listTickets(),
    refetchInterval: 5_000,
  });

  const { data: stats } = useQuery({
    queryKey: ["ticket-stats"],
    queryFn: getTicketStats,
    refetchInterval: 10_000,
  });

  const allTickets = tickets || [];
  const escalatedTickets = allTickets.filter(
    (t) => t.session_id && (t.status === "Open" || t.status === "In Progress")
  );
  const resolvedTickets = allTickets.filter(
    (t) => t.status === "Resolved" || t.status === "Closed"
  );
  const p1Count = allTickets.filter((t) => t.priority === "P1" && t.status !== "Closed").length;

  const priorityColors: Record<string, string> = {
    P1: "bg-red-500",
    P2: "bg-orange-500",
    P3: "bg-yellow-500",
    P4: "bg-blue-400",
  };
  const statusColors: Record<string, string> = {
    Open: "bg-blue-500",
    "In Progress": "bg-amber-500",
    Resolved: "bg-green-500",
    Closed: "bg-gray-400",
  };

  return (
    <div className="flex min-h-screen w-full bg-background">
      {/* ══════════ Ops Sidebar ══════════ */}
      <div className="hidden lg:flex">
        <OpsSidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      </div>

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* ── Header ─────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 md:px-8 py-3 md:py-4 border-b border-border bg-card">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center shadow-sm shrink-0">
            <Headset className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold tracking-tight">IT Assist Dashboard</h1>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Manage escalated tickets &middot; Intervene in user conversations
            </p>
          </div>
          {/* Mobile: back to list */}
          {selectedTicket && (
            <button
              onClick={() => { setSelectedTicket(null); setMobilePanel("list"); }}
              className="md:hidden p-2 rounded-lg hover:bg-accent text-muted-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="w-3.5 h-3.5 text-green-500" />
            <span className="hidden sm:inline">Live</span>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* ══════════ Left panel ══════════ */}
          <div className={`w-full md:w-[400px] lg:w-[420px] border-r border-border flex flex-col overflow-hidden bg-background ${mobilePanel === "detail" && selectedTicket ? "hidden md:flex" : "flex"}`}>
            {/* KPIs */}
            <div className="px-4 py-3 border-b border-border space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <KPICard
                  label="Escalated"
                  value={escalatedTickets.length}
                  icon={AlertTriangle}
                  color="bg-red-500"
                  sub="Needs attention"
                />
                <KPICard
                  label="In Progress"
                  value={stats?.in_progress ?? 0}
                  icon={Clock}
                  color="bg-amber-500"
                  sub="Being handled"
                />
                <KPICard
                  label="Resolved"
                  value={stats?.resolved ?? 0}
                  icon={CheckCircle2}
                  color="bg-green-500"
                  sub="Completed"
                />
                <KPICard
                  label="Critical (P1)"
                  value={p1Count}
                  icon={TrendingUp}
                  color={p1Count > 0 ? "bg-red-600" : "bg-gray-400"}
                  sub={p1Count > 0 ? "Immediate action" : "None active"}
                />
              </div>

              {/* Distribution bars */}
              <div className="grid grid-cols-2 gap-2">
                <MiniDistribution
                  title="By Priority"
                  data={stats?.by_priority ?? {}}
                  colors={priorityColors}
                />
                <MiniDistribution
                  title="By Status"
                  data={stats?.by_status ?? {}}
                  colors={statusColors}
                />
              </div>
            </div>

            {/* Ticket list */}
            <div className="px-5 py-3 border-b border-border flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Escalated Tickets ({escalatedTickets.length})
              </p>
            </div>
            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="p-5 space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-xl" />)}
                </div>
              ) : escalatedTickets.length === 0 ? (
                <div className="p-10 text-center text-muted-foreground text-sm">
                  <Headset className="w-12 h-12 mx-auto mb-3 opacity-20" />
                  <p className="font-medium">No escalated tickets</p>
                  <p className="text-xs mt-1 text-muted-foreground/70">Tickets requiring human action will appear here</p>
                </div>
              ) : (
                <div className="p-3 space-y-2">
                  {escalatedTickets.map((ticket) => (
                    <button
                      key={ticket.ticket_id}
                      onClick={() => { setSelectedTicket(ticket); setMobilePanel("detail"); }}
                      className={`w-full text-left px-4 py-3.5 rounded-xl border transition-all ${
                        selectedTicket?.ticket_id === ticket.ticket_id
                          ? "bg-accent border-primary/30 shadow-sm"
                          : "bg-card border-border hover:border-primary/20 hover:shadow-sm"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono text-xs font-bold text-primary">{ticket.ticket_id}</span>
                        <PriorityChip priority={ticket.priority} />
                      </div>
                      <p className="text-sm font-medium truncate leading-snug">{ticket.summary}</p>
                      <div className="flex items-center justify-between mt-2">
                        <StatusChip status={ticket.status} />
                        <span className="text-[10px] text-muted-foreground">
                          {ticket.created_at ? formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true }) : ""}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Resolved section */}
              {resolvedTickets.length > 0 && (
                <>
                  <div className="px-5 py-3 border-t border-b border-border">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Resolved ({resolvedTickets.length})
                    </p>
                  </div>
                  <div className="p-3 space-y-1 opacity-60">
                    {resolvedTickets.slice(0, 10).map((ticket) => (
                      <button
                        key={ticket.ticket_id}
                        onClick={() => setSelectedTicket(ticket)}
                        className={`w-full text-left px-4 py-2.5 rounded-lg hover:bg-accent/50 transition-colors ${
                          selectedTicket?.ticket_id === ticket.ticket_id ? "bg-accent" : ""
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xs font-medium text-primary">{ticket.ticket_id}</span>
                          <span className="text-xs truncate flex-1">{ticket.summary}</span>
                          <StatusChip status={ticket.status} />
                        </div>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ══════════ Right panel ══════════ */}
          <div className={`flex-1 flex flex-col overflow-hidden ${mobilePanel === "list" || !selectedTicket ? "hidden md:flex" : "flex"}`}>
            {selectedTicket ? (
              <TicketDetailPanel
                ticket={selectedTicket}
                onUpdate={(updated) => {
                  setSelectedTicket(updated);
                  queryClient.invalidateQueries({ queryKey: ["tickets"] });
                  queryClient.invalidateQueries({ queryKey: ["ticket-stats"] });
                }}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <MessageSquare className="w-14 h-14 mx-auto mb-4 opacity-15" />
                  <p className="text-sm font-medium">Select a ticket to view details</p>
                  <p className="text-xs text-muted-foreground/70 mt-1">Chat with users and manage escalations</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ─── Quick reply templates ──────────────────────────────────────

const REPLY_TEMPLATES: { category: string; icon: React.ElementType; color: string; templates: string[] }[] = [
  {
    category: "Greeting & Intro",
    icon: MessageSquare,
    color: "bg-blue-500",
    templates: [
      "Hi there! I'm from IT Support. I'll be assisting you with this issue today.",
      "Hello! I've picked up your ticket and I'm looking into it now.",
      "Thanks for reaching out. Let me review your issue and get back to you shortly.",
    ],
  },
  {
    category: "Troubleshooting",
    icon: Wrench,
    color: "bg-orange-500",
    templates: [
      "Could you try restarting your device and let me know if the issue persists?",
      "Please try clearing your browser cache and cookies, then attempt again.",
      "Can you check if you're connected to the VPN and try once more?",
      "Please go to Settings > Update & Security and check for pending updates.",
      "Try signing out and signing back in to refresh your session.",
    ],
  },
  {
    category: "Account & Access",
    icon: ShieldCheck,
    color: "bg-green-500",
    templates: [
      "I've reset your password. You should receive an email with instructions shortly.",
      "Your account has been unlocked. Please try logging in again.",
      "I've granted the requested access permissions. It may take a few minutes to propagate.",
      "For security reasons, please enable MFA on your account. I can walk you through it.",
    ],
  },
  {
    category: "Status Update",
    icon: RotateCcw,
    color: "bg-violet-500",
    templates: [
      "I'm still working on this. I'll update you as soon as I have more information.",
      "This has been escalated to our senior team. They'll reach out to you shortly.",
      "The issue has been identified and a fix is being deployed. ETA: ~30 minutes.",
      "This is a known issue affecting multiple users. Our team is actively working on a fix.",
    ],
  },
  {
    category: "Resolution & Closing",
    icon: CheckCircle2,
    color: "bg-emerald-500",
    templates: [
      "The issue has been resolved. Please verify on your end and let me know if it's working.",
      "I've applied the fix. Could you test it out and confirm everything looks good?",
      "Glad I could help! If you run into any other issues, don't hesitate to open a new ticket.",
      "This ticket will be closed now. Feel free to reopen if the issue recurs.",
    ],
  },
  {
    category: "Request Info",
    icon: HelpCircle,
    color: "bg-amber-500",
    templates: [
      "Could you provide a screenshot of the error you're seeing?",
      "What browser and OS version are you currently using?",
      "When did this issue first start? Was there any recent change on your end?",
      "Can you share the exact error message you're receiving?",
    ],
  },
];

function QuickReplyPicker({ onSelect }: { onSelect: (text: string) => void }) {
  const [open, setOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (
        popoverRef.current && !popoverRef.current.contains(e.target as Node) &&
        triggerRef.current && !triggerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setActiveCategory(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (!open || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setPos({
      top: rect.top - 8,
      left: Math.max(8, rect.right - 340),
    });
  }, [open]);

  const active = REPLY_TEMPLATES.find((c) => c.category === activeCategory);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => { setOpen(!open); setActiveCategory(null); }}
        className="p-2.5 rounded-xl border border-input bg-background hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
        title="Quick replies"
      >
        <MoreHorizontal className="w-4 h-4" />
      </button>

      {open && createPortal(
        <div
          ref={popoverRef}
          className="fixed w-[340px] max-h-[380px] bg-card border border-border rounded-xl shadow-xl overflow-hidden z-[9999] flex flex-col"
          style={{ top: pos.top, left: pos.left, transform: "translateY(-100%)" }}
        >
          <div className="px-3 py-2 border-b border-border bg-muted/30">
            <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              {activeCategory ? (
                <button
                  onClick={() => setActiveCategory(null)}
                  className="flex items-center gap-1.5 hover:text-foreground transition-colors"
                >
                  <ChevronDown className="w-3 h-3 rotate-90" />
                  {activeCategory}
                </button>
              ) : (
                "Quick Replies"
              )}
            </p>
          </div>

          <div className="overflow-y-auto flex-1">
            {!activeCategory ? (
              <div className="p-1.5">
                {REPLY_TEMPLATES.map((cat) => {
                  const Icon = cat.icon;
                  return (
                    <button
                      key={cat.category}
                      onClick={() => setActiveCategory(cat.category)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-accent/70 transition-colors text-left"
                    >
                      <div className={`w-7 h-7 rounded-lg ${cat.color} flex items-center justify-center shrink-0`}>
                        <Icon className="w-3.5 h-3.5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground">{cat.category}</p>
                        <p className="text-[10px] text-muted-foreground">{cat.templates.length} templates</p>
                      </div>
                      <ChevronDown className="w-3.5 h-3.5 text-muted-foreground -rotate-90" />
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="p-1.5">
                {active?.templates.map((tpl, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      onSelect(tpl);
                      setOpen(false);
                      setActiveCategory(null);
                    }}
                    className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-accent/70 transition-colors"
                  >
                    <p className="text-xs text-foreground leading-relaxed">{tpl}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}

// ─── Ticket detail + chat panel ─────────────────────────────────

function TicketDetailPanel({
  ticket,
  onUpdate,
}: {
  ticket: Ticket;
  onUpdate: (t: Ticket) => void;
}) {
  const [replyText, setReplyText] = useState("");
  const [noteText, setNoteText] = useState("");
  const [showDetails, setShowDetails] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const sessionId = ticket.session_id;

  // ── Agent pause/resume toggle ──
  const { data: agentStatusData, refetch: refetchAgentStatus } = useQuery({
    queryKey: ["agent-status", sessionId],
    queryFn: () => getAgentStatus(sessionId!),
    enabled: !!sessionId,
  });
  const agentPaused = agentStatusData?.paused ?? false;

  const pauseMutation = useMutation({
    mutationFn: () => (agentPaused ? resumeAgent(sessionId!) : pauseAgent(sessionId!)),
    onSuccess: () => refetchAgentStatus(),
  });

  // Load initial history
  const { data: historyData, refetch: refetchHistory } = useQuery({
    queryKey: ["session-history", sessionId],
    queryFn: () => getSessionHistory(sessionId!),
    enabled: !!sessionId,
  });

  // Real-time: when a WS message arrives, refetch history from server
  // This avoids duplicates between baseHistory and liveMessages
  useSessionWS(sessionId, useCallback(() => {
    refetchHistory();
  }, [refetchHistory]));

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Ticket>) => updateTicket(ticket.ticket_id, data),
    onSuccess: (res) => onUpdate(res.ticket),
  });

  const replyMutation = useMutation({
    mutationFn: (message: string) =>
      agentReply({ session_id: sessionId!, message, agent_name: "IT Support" }),
    onSuccess: () => {
      setReplyText("");
      refetchHistory();
    },
  });

  const history = historyData?.history || [];

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history.length]);

  const handleSendReply = () => {
    const trimmed = replyText.trim();
    if (!trimmed || !sessionId) return;
    replyMutation.mutate(trimmed);
  };

  const handleAddNote = () => {
    const trimmed = noteText.trim();
    if (!trimmed) return;
    updateMutation.mutate({ notes: trimmed } as any);
    setNoteText("");
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* ── Ticket header ─── */}
      <div className="px-4 md:px-6 py-3 border-b border-border bg-card shrink-0">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-mono text-xs font-bold text-primary">{ticket.ticket_id}</span>
            <PriorityChip priority={ticket.priority} />
            <StatusChip status={ticket.status} />
            <span className="text-xs font-medium truncate ml-1 hidden sm:inline">{ticket.summary}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {/* Agent toggle */}
            {sessionId && (
              <button
                onClick={() => pauseMutation.mutate()}
                disabled={pauseMutation.isPending}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                  agentPaused
                    ? "bg-red-500/10 text-red-600 border-red-500/30 hover:bg-red-500/20"
                    : "bg-green-500/10 text-green-600 border-green-500/30 hover:bg-green-500/20"
                }`}
                title={agentPaused ? "AI Agent is paused — click to resume" : "AI Agent is active — click to pause"}
              >
                {pauseMutation.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : agentPaused ? (
                  <ToggleLeft className="w-4 h-4" />
                ) : (
                  <ToggleRight className="w-4 h-4" />
                )}
                AI Agent {agentPaused ? "Paused" : "Active"}
              </button>
            )}
            <select
              className="text-xs bg-background border border-input rounded-lg px-2.5 py-1.5"
              value={ticket.status}
              onChange={(e) => updateMutation.mutate({ status: e.target.value as Ticket["status"] })}
            >
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
              <option value="Closed">Closed</option>
            </select>
            <select
              className="text-xs bg-background border border-input rounded-lg px-2.5 py-1.5"
              value={ticket.priority}
              onChange={(e) => updateMutation.mutate({ priority: e.target.value as Ticket["priority"] })}
            >
              <option value="P1">P1 — Critical</option>
              <option value="P2">P2 — High</option>
              <option value="P3">P3 — Medium</option>
              <option value="P4">P4 — Low</option>
            </select>
          </div>
        </div>

        {/* Collapsible details */}
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-2"
        >
          {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          Ticket Details
        </button>
        {showDetails && (
          <div className="text-xs space-y-2 text-muted-foreground mt-3 max-h-[200px] overflow-y-auto border-t border-border pt-3">
            {ticket.description && <p className="leading-relaxed">{ticket.description}</p>}
            <div className="flex gap-5">
              <span>Category: <strong className="text-foreground">{ticket.category}</strong></span>
              <span>Assigned: <strong className="text-foreground">{ticket.assigned_to}</strong></span>
              <span>User: <strong className="text-foreground">{ticket.user_name || "Unknown"}</strong></span>
            </div>
            {ticket.troubleshooting_steps_completed && ticket.troubleshooting_steps_completed.length > 0 && (
              <div>
                <p className="font-semibold text-foreground mt-1">Steps completed by AI:</p>
                <ul className="list-disc list-inside ml-2 space-y-0.5">
                  {ticket.troubleshooting_steps_completed.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
            {ticket.notes && ticket.notes.length > 0 && (
              <div>
                <p className="font-semibold text-foreground mt-1">Notes:</p>
                {ticket.notes.map((n, i) => (
                  <p key={i} className="ml-2">
                    {typeof n === "string" ? n : `${(n as any).text} (${formatDistanceToNow(new Date((n as any).timestamp), { addSuffix: true })})`}
                  </p>
                ))}
              </div>
            )}
            <div className="flex gap-2 mt-2">
              <input
                className="flex-1 bg-background border border-input rounded-lg px-3 py-1.5 text-xs"
                placeholder="Add internal note..."
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleAddNote(); }}
              />
              <button
                onClick={handleAddNote}
                disabled={!noteText.trim()}
                className="text-xs px-3 py-1.5 bg-muted rounded-lg hover:bg-accent disabled:opacity-50"
              >
                Add Note
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Agent paused banner ─── */}
      {agentPaused && (
        <div className="px-6 py-2 bg-red-500/10 border-b border-red-500/20 flex items-center gap-2 text-xs text-red-600 shrink-0">
          <ToggleLeft className="w-3.5 h-3.5" />
          <span className="font-medium">AI Agent is paused for this session.</span>
          <span className="text-red-500/70">User messages will not receive automatic replies.</span>
        </div>
      )}

      {/* ── Conversation header ─── */}
      <div className="px-6 py-2.5 border-b border-border bg-muted/30 flex items-center justify-between shrink-0">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Conversation
        </p>
        <button onClick={() => refetchHistory()} className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-accent transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* ── Chat messages ─── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-5 space-y-3 min-h-0">
        {!sessionId ? (
          <p className="text-sm text-muted-foreground text-center py-8">No session linked to this ticket</p>
        ) : history.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">Loading conversation...</p>
        ) : (
          history.map((msg: Message, i: number) => {
            const isUser = msg.role === "user";
            const isHumanAgent = msg.metadata?.intent === "human_agent";
            return (
              <div key={i} className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  isUser ? "bg-blue-500" : isHumanAgent ? "bg-orange-500" : "bg-primary"
                }`}>
                  {isUser ? (
                    <User className="w-4 h-4 text-white" />
                  ) : isHumanAgent ? (
                    <Headset className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-primary-foreground" />
                  )}
                </div>
                <div className={`max-w-[70%] ${isUser ? "text-right" : ""}`}>
                  {isHumanAgent && (
                    <p className="text-[10px] text-orange-500 font-semibold mb-0.5">
                      {(msg.metadata as any)?.agent_name || "IT Support"}
                    </p>
                  )}
                  <div
                    className={`inline-block px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                      isUser
                        ? "bg-blue-500/15 text-foreground rounded-br-sm"
                        : isHumanAgent
                        ? "bg-orange-500/10 text-foreground rounded-bl-sm border border-orange-500/20"
                        : "bg-accent text-foreground rounded-bl-sm"
                    }`}
                  >
                    {msg.content}
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">
                    {msg.timestamp ? formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true }) : ""}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* ── Reply input ─── */}
      {sessionId && (ticket.status === "Open" || ticket.status === "In Progress") && (
        <div className="px-6 py-3.5 border-t border-border bg-card shrink-0">
          <div className="flex gap-2.5">
            <QuickReplyPicker onSelect={(text) => setReplyText(text)} />
            <input
              className="flex-1 bg-background border border-input rounded-xl px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-shadow"
              placeholder="Reply as IT Support Agent..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendReply();
                }
              }}
              disabled={replyMutation.isPending}
            />
            <button
              onClick={handleSendReply}
              disabled={!replyText.trim() || replyMutation.isPending}
              className="bg-orange-500 text-white rounded-xl px-5 py-2.5 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {replyMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          <p className="text-[10px] text-muted-foreground mt-2">
            Your message will appear in the user&apos;s chat as <strong className="text-orange-500">IT Support</strong>
          </p>
        </div>
      )}
    </div>
  );
}
