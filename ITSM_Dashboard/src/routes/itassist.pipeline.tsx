import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow, format } from "date-fns";
import {
  Terminal, ChevronDown, ChevronRight, RefreshCw,
  ArrowLeft, Search, Activity, Zap, Clock,
  MessageSquare, Ticket, Brain, Database,
} from "lucide-react";
import { getPipelineLogs } from "@/lib/api";
import type { PipelineEvent } from "@/lib/types";

export const Route = createFileRoute("/itassist/pipeline")({
  component: PipelineLogsDashboard,
});

const EVENT_ICONS: Record<string, React.ElementType> = {
  message_received: MessageSquare,
  kb_retrieved: Database,
  llm_response: Brain,
  ticket_created: Ticket,
  cache_hit: Zap,
};

const EVENT_COLORS: Record<string, string> = {
  message_received: "bg-blue-500",
  kb_retrieved: "bg-purple-500",
  llm_response: "bg-green-500",
  ticket_created: "bg-orange-500",
  cache_hit: "bg-yellow-500",
};

function PipelineLogsDashboard() {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["pipeline-logs-full"],
    queryFn: () => getPipelineLogs(300),
    refetchInterval: 5_000,
  });

  const events = data?.events ?? [];

  const eventTypes = Array.from(new Set(events.map((e) => e.event_type))).sort();

  const filtered = events.filter((e) => {
    if (filterType !== "all" && e.event_type !== filterType) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        e.event_type?.toLowerCase().includes(q) ||
        e.session_id?.toLowerCase().includes(q) ||
        JSON.stringify(e.data)?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const typeCounts: Record<string, number> = {};
  events.forEach((e) => {
    typeCounts[e.event_type] = (typeCounts[e.event_type] || 0) + 1;
  });

  const now = Date.now();
  const last10min = events.filter(
    (e) => e.timestamp && now - new Date(e.timestamp).getTime() < 600_000
  ).length;

  return (
    <div className="flex min-h-screen w-full bg-background">
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <div className="flex items-center gap-3 px-4 md:px-8 py-3 md:py-4 border-b border-border bg-card">
          <Link
            to="/itassist/dashboard"
            className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center shadow-sm shrink-0">
            <Terminal className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold tracking-tight">Pipeline Logs</h1>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Monitor AI pipeline events &middot; {events.length} total events
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="w-3.5 h-3.5 text-green-500" />
            <span className="hidden sm:inline">Auto-refresh</span>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="hidden lg:flex w-[260px] border-r border-border flex-col bg-card overflow-y-auto">
            <div className="p-4 border-b border-border">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">Throughput</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-foreground">{last10min}</span>
                <span className="text-[10px] text-muted-foreground">events / 10 min</span>
              </div>
            </div>

            <div className="p-4 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Event Types</p>
              <div className="space-y-2">
                {Object.entries(typeCounts).sort(([, a], [, b]) => b - a).map(([type, count]) => {
                  const Icon = EVENT_ICONS[type] || Activity;
                  const color = EVENT_COLORS[type] || "bg-gray-500";
                  return (
                    <button
                      key={type}
                      onClick={() => setFilterType(filterType === type ? "all" : type)}
                      className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-colors ${filterType === type ? "bg-accent" : "hover:bg-accent/50"}`}
                    >
                      <div className={`w-5 h-5 rounded ${color} flex items-center justify-center`}>
                        <Icon className="w-3 h-3 text-white" />
                      </div>
                      <span className="text-xs text-foreground flex-1 truncate">{type.replace(/_/g, " ")}</span>
                      <span className="text-[10px] font-bold text-muted-foreground">{count}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 border-b border-border bg-card flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search pipeline events..."
                  className="w-full pl-9 pr-4 py-2 text-xs bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="lg:hidden px-3 py-2 text-xs bg-background border border-border rounded-lg focus:outline-none"
              >
                <option value="all">All types</option>
                {eventTypes.map((t) => (
                  <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
                ))}
              </select>
              <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                {filtered.length} of {events.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center h-40">
                  <RefreshCw className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
              ) : filtered.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <Terminal className="w-8 h-8 mb-2" />
                  <p className="text-sm font-medium">No events found</p>
                  <p className="text-xs">{search || filterType !== "all" ? "Try adjusting filters" : "Waiting for pipeline activity"}</p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {filtered.map((evt, idx) => {
                    const Icon = EVENT_ICONS[evt.event_type] || Activity;
                    const color = EVENT_COLORS[evt.event_type] || "bg-gray-500";
                    const isExpanded = expandedIdx === idx;

                    return (
                      <button
                        key={`${evt.timestamp}-${idx}`}
                        onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                        className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-accent/50 transition-colors"
                      >
                        <div className={`w-6 h-6 rounded ${color} flex items-center justify-center shrink-0 mt-0.5`}>
                          <Icon className="w-3 h-3 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className="text-xs font-medium text-foreground">{evt.event_type.replace(/_/g, " ")}</span>
                            {evt.session_id && (
                              <span className="text-[10px] text-muted-foreground font-mono truncate max-w-[120px]">{evt.session_id}</span>
                            )}
                          </div>
                          {evt.timestamp && (
                            <p className="text-[10px] text-muted-foreground">
                              {formatDistanceToNow(new Date(evt.timestamp), { addSuffix: true })}
                              {" · "}
                              {format(new Date(evt.timestamp), "HH:mm:ss.SSS")}
                            </p>
                          )}
                          {isExpanded && evt.data && (
                            <pre className="mt-2 text-[11px] text-muted-foreground bg-muted rounded-lg p-3 overflow-x-auto whitespace-pre-wrap font-mono max-h-48">
                              {JSON.stringify(evt.data, null, 2)}
                            </pre>
                          )}
                        </div>
                        <div className="mt-1">
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}