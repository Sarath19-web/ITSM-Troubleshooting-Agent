import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow, format } from "date-fns";
import {
  AlertTriangle, ChevronDown, ChevronRight, RefreshCw,
  ArrowLeft, Search, CheckCircle2, XCircle,
  Activity,
} from "lucide-react";
import { getErrorLogs, type ErrorLogEntry } from "@/lib/api";

export const Route = createFileRoute("/itassist/errors")({
  component: ErrorLogsDashboard,
});

function ErrorLogsDashboard() {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  const { data, isLoading, refetch, dataUpdatedAt } = useQuery({
    queryKey: ["error-logs-full"],
    queryFn: () => getErrorLogs(200),
    refetchInterval: 8_000,
  });

  const errors = data?.errors ?? [];
  const filtered = search
    ? errors.filter(
        (e) =>
          e.message?.toLowerCase().includes(search.toLowerCase()) ||
          e.session_id?.toLowerCase().includes(search.toLowerCase()) ||
          e.exception?.toLowerCase().includes(search.toLowerCase()) ||
          e.logger?.toLowerCase().includes(search.toLowerCase())
      )
    : errors;

  const hourCounts: Record<string, number> = {};
  errors.forEach((e) => {
    if (!e.timestamp) return;
    const h = format(new Date(e.timestamp), "MMM d, HH:00");
    hourCounts[h] = (hourCounts[h] || 0) + 1;
  });
  const recentHours = Object.entries(hourCounts).slice(-8);
  const maxCount = Math.max(...recentHours.map(([, c]) => c), 1);

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
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center shadow-sm shrink-0">
            <AlertTriangle className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold tracking-tight">Error Logs</h1>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Monitor application errors &middot; {errors.length} total entries
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
          <div className="hidden lg:flex w-[280px] border-r border-border flex-col bg-card overflow-y-auto">
            <div className="p-4 border-b border-border">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">Error Rate (by hour)</p>
              {recentHours.length === 0 ? (
                <p className="text-xs text-muted-foreground">No data</p>
              ) : (
                <div className="space-y-1.5">
                  {recentHours.map(([hour, count]) => (
                    <div key={hour} className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground w-[80px] shrink-0 truncate">{hour.split(", ")[1] || hour}</span>
                      <div className="flex-1 h-2.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-500 rounded-full transition-all"
                          style={{ width: `${(count / maxCount) * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-bold text-foreground w-6 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Quick Stats</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Total errors</span>
                  <span className="text-xs font-bold text-foreground">{errors.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Unique loggers</span>
                  <span className="text-xs font-bold text-foreground">
                    {new Set(errors.map((e) => e.logger)).size}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">With exceptions</span>
                  <span className="text-xs font-bold text-foreground">
                    {errors.filter((e) => e.exception).length}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 border-b border-border bg-card">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search errors by message, logger, exception, session..."
                  className="w-full pl-9 pr-4 py-2 text-xs bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <div className="flex items-center justify-between mt-1.5">
                <span className="text-[10px] text-muted-foreground">
                  {filtered.length} of {errors.length} entries
                </span>
                {dataUpdatedAt ? (
                  <span className="text-[10px] text-muted-foreground">
                    Updated {formatDistanceToNow(new Date(dataUpdatedAt), { addSuffix: true })}
                  </span>
                ) : null}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center h-40">
                  <RefreshCw className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
              ) : filtered.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <CheckCircle2 className="w-8 h-8 mb-2 text-green-500" />
                  <p className="text-sm font-medium">No errors found</p>
                  <p className="text-xs">{search ? "Try a different search" : "System is running smoothly"}</p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {filtered.map((err, idx) => (
                    <ErrorEntry
                      key={`${err.timestamp}-${idx}`}
                      entry={err}
                      expanded={expandedIdx === idx}
                      onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ErrorEntry({
  entry,
  expanded,
  onToggle,
}: {
  entry: ErrorLogEntry;
  expanded: boolean;
  onToggle: () => void;
}) {
  const levelColor =
    entry.level === "ERROR"
      ? "text-red-500 bg-red-500/10"
      : entry.level === "WARNING"
        ? "text-yellow-500 bg-yellow-500/10"
        : "text-blue-500 bg-blue-500/10";

  return (
    <div className="group">
      <button
        onClick={onToggle}
        className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-accent/50 transition-colors"
      >
        <div className="mt-0.5">
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${levelColor}`}>
              {entry.level}
            </span>
            <span className="text-[10px] text-muted-foreground truncate">{entry.logger}</span>
            {entry.module && (
              <span className="text-[10px] text-muted-foreground">
                {entry.module}
                {entry.function ? `.${entry.function}` : ""}
                {entry.line ? `:${entry.line}` : ""}
              </span>
            )}
          </div>
          <p className="text-xs text-foreground truncate">{entry.message}</p>
          {entry.timestamp && (
            <p className="text-[10px] text-muted-foreground mt-1">
              {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
              {" · "}
              {format(new Date(entry.timestamp), "MMM d, HH:mm:ss")}
            </p>
          )}
        </div>
        {entry.exception && (
          <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-1" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-3 pl-11 space-y-2">
          {entry.session_id && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase mb-0.5">Session</p>
              <p className="text-xs text-foreground font-mono">{entry.session_id}</p>
            </div>
          )}
          {entry.exception && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase mb-0.5">Exception</p>
              <pre className="text-[11px] text-red-400 bg-red-500/5 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap font-mono max-h-48">
                {entry.exception}
              </pre>
            </div>
          )}
          <div>
            <p className="text-[10px] font-semibold text-muted-foreground uppercase mb-0.5">Full Message</p>
            <p className="text-xs text-foreground">{entry.message}</p>
          </div>
        </div>
      )}
    </div>
  );
}