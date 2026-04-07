import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { AppSidebar } from "@/components/AppSidebar";
import { getPipelineLogs, getAccessLogs, getErrorLogs } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronDown, ChevronRight } from "lucide-react";

export const Route = createFileRoute("/logs")({
  component: LogsPage,
});

const EVENT_COLORS: Record<string, string> = {
  message_received: "bg-info/15 text-info",
  cache_hit: "bg-success/15 text-success",
  kb_retrieved: "bg-primary/15 text-primary",
  llm_response: "bg-accent text-accent-foreground",
  ticket_created: "bg-warning/15 text-warning",
  llm_error: "bg-danger/15 text-danger",
};

function LogsPage() {
  const [tab, setTab] = useState<"pipeline" | "access" | "errors">("pipeline");
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null);
  const [expandedError, setExpandedError] = useState<number | null>(null);
  const [sessionFilter, setSessionFilter] = useState("");

  const tabs = [
    { key: "pipeline" as const, label: "Pipeline Events" },
    { key: "access" as const, label: "API Access Log" },
    { key: "errors" as const, label: "Errors" },
  ];

  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6 max-w-[1400px]">
          <h1 className="text-2xl font-semibold">Logs & Observability</h1>
          <div className="flex gap-2 border-b border-border">
            {tabs.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  tab === t.key ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "pipeline" && <PipelineTab sessionFilter={sessionFilter} onSessionFilterChange={setSessionFilter} expandedEvent={expandedEvent} onToggleEvent={setExpandedEvent} />}
          {tab === "access" && <AccessTab />}
          {tab === "errors" && <ErrorsTab expandedError={expandedError} onToggleError={setExpandedError} />}
        </div>
      </main>
    </div>
  );
}

function PipelineTab({ sessionFilter, onSessionFilterChange, expandedEvent, onToggleEvent }: {
  sessionFilter: string;
  onSessionFilterChange: (v: string) => void;
  expandedEvent: number | null;
  onToggleEvent: (v: number | null) => void;
}) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["pipeline-logs", sessionFilter],
    queryFn: () => getPipelineLogs(100, sessionFilter || undefined),
    refetchInterval: 5_000,
  });

  if (isLoading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>;
  if (isError) return <div className="text-center py-8"><p className="text-sm text-muted-foreground">Failed to load pipeline logs</p><button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button></div>;

  const events = data?.events || [];

  return (
    <div className="space-y-3">
      <input
        className="bg-background border border-input rounded-lg px-3 py-2 text-sm w-64"
        placeholder="Filter by session ID..."
        value={sessionFilter}
        onChange={(e) => onSessionFilterChange(e.target.value)}
      />
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No pipeline events</p>
      ) : (
        <div className="space-y-1">
          {events.map((evt, i) => (
            <div key={i} className="bg-card rounded-lg border border-border">
              <button
                className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm"
                onClick={() => onToggleEvent(expandedEvent === i ? null : i)}
              >
                {expandedEvent === i ? <ChevronDown className="w-3 h-3 shrink-0" /> : <ChevronRight className="w-3 h-3 shrink-0" />}
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${EVENT_COLORS[evt.event_type] || "bg-muted text-muted-foreground"}`}>
                  {evt.event_type}
                </span>
                <span className="text-xs text-muted-foreground truncate">{evt.session_id || "—"}</span>
                <span className="text-xs text-muted-foreground ml-auto">{evt.timestamp ? formatDistanceToNow(new Date(evt.timestamp), { addSuffix: true }) : ""}</span>
              </button>
              {expandedEvent === i && (
                <pre className="px-4 pb-3 text-xs font-mono text-muted-foreground overflow-x-auto max-h-48">
                  {JSON.stringify(evt.data, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AccessTab() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["access-logs"],
    queryFn: () => getAccessLogs(100),
    refetchInterval: 5_000,
  });

  if (isLoading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>;
  if (isError) return <div className="text-center py-8"><p className="text-sm text-muted-foreground">Failed to load access logs</p><button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button></div>;

  const requests = data?.requests || [];

  return (
    <div className="bg-card rounded-xl border border-border overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="px-4 py-3 font-medium">Timestamp</th>
            <th className="px-4 py-3 font-medium">Method</th>
            <th className="px-4 py-3 font-medium">Path</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Duration</th>
          </tr>
        </thead>
        <tbody>
          {requests.length === 0 ? (
            <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No access logs</td></tr>
          ) : requests.map((req, i) => {
            const isError = req.status_code >= 400;
            const isSlow = req.duration_ms > 5000;
            return (
              <tr key={i} className={`border-b border-border ${isError ? "bg-danger/5" : isSlow ? "bg-warning/5" : ""}`}>
                <td className="px-4 py-2 text-xs text-muted-foreground">{req.timestamp ? formatDistanceToNow(new Date(req.timestamp), { addSuffix: true }) : "—"}</td>
                <td className="px-4 py-2 font-mono text-xs font-semibold">{req.method}</td>
                <td className="px-4 py-2 font-mono text-xs">{req.path}</td>
                <td className={`px-4 py-2 font-mono text-xs font-semibold ${isError ? "text-danger" : "text-success"}`}>{req.status_code}</td>
                <td className={`px-4 py-2 text-xs ${isSlow ? "text-warning font-semibold" : "text-muted-foreground"}`}>{req.duration_ms}ms</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ErrorsTab({ expandedError, onToggleError }: { expandedError: number | null; onToggleError: (v: number | null) => void }) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["error-logs"],
    queryFn: () => getErrorLogs(100),
    refetchInterval: 10_000,
  });

  if (isLoading) return <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>;
  if (isError) return <div className="text-center py-8"><p className="text-sm text-muted-foreground">Failed to load error logs</p><button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button></div>;

  const errors = data?.errors || [];

  return (
    <div className="space-y-1">
      {errors.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No errors — looking good! ✓</p>
      ) : errors.map((err, i) => (
        <div key={i} className="bg-card rounded-lg border border-border border-l-4 border-l-danger">
          <button
            className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm"
            onClick={() => onToggleError(expandedError === i ? null : i)}
          >
            {expandedError === i ? <ChevronDown className="w-3 h-3 shrink-0" /> : <ChevronRight className="w-3 h-3 shrink-0" />}
            <span className="text-sm text-danger truncate flex-1">{err.error}</span>
            <span className="text-xs text-muted-foreground">{err.timestamp ? formatDistanceToNow(new Date(err.timestamp), { addSuffix: true }) : ""}</span>
          </button>
          {expandedError === i && err.stack_trace && (
            <pre className="px-4 pb-3 text-xs font-mono text-muted-foreground overflow-x-auto max-h-48 whitespace-pre-wrap">
              {err.stack_trace}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
