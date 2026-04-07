import { useState } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, LayoutDashboard, FileText, ChevronLeft, ChevronRight, Bot, RefreshCw, Loader2 } from "lucide-react";
import { getHealth, getCacheStats, listSessions } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export function AppSidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { label: "Chat", to: "/", icon: MessageSquare },
    { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
    { label: "Logs", to: "/logs", icon: FileText },
  ];

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  const { data: cacheStats, isLoading: cacheLoading } = useQuery({
    queryKey: ["cache-stats"],
    queryFn: getCacheStats,
  });

  const { data: sessionsData, isLoading: sessionsLoading, refetch: refetchSessions } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => listSessions(10),
  });

  return (
    <aside
      className={`flex flex-col bg-sidebar-bg text-sidebar-foreground transition-all duration-300 ${collapsed ? "w-16" : "w-[280px]"} shrink-0 h-screen sticky top-0`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-sidebar-border">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
          <Bot className="w-5 h-5 text-primary-foreground" />
        </div>
        {!collapsed && <span className="font-semibold text-base tracking-tight">IT Service Desk</span>}
      </div>

      {/* Navigation */}
      <nav className="px-2 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              }`}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Recent Sessions */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">Recent Sessions</p>
            <button onClick={() => refetchSessions()} className="text-sidebar-foreground/50 hover:text-sidebar-foreground">
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
          {sessionsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-8 w-full bg-sidebar-accent/30" />
              <Skeleton className="h-8 w-full bg-sidebar-accent/30" />
            </div>
          ) : sessionsData?.sessions && sessionsData.sessions.length > 0 ? (
            <div className="space-y-1">
              {sessionsData.sessions.map((s) => (
                <Link
                  key={s.session_id}
                  to="/"
                  search={{ sessionId: s.session_id }}
                  className="text-xs text-sidebar-foreground/70 px-2 py-1.5 rounded hover:bg-sidebar-accent/50 cursor-pointer truncate block hover:text-sidebar-foreground transition-colors"
                  title={s.label || s.session_id}
                >
                  {s.label || s.session_id} <span className="text-sidebar-foreground/40">({s.message_count})</span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-xs text-sidebar-foreground/40">No sessions yet</p>
          )}
        </div>
      )}

      {/* Cache Stats */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50 mb-2">Cache Stats</p>
          {cacheLoading ? (
            <Skeleton className="h-8 w-full bg-sidebar-accent/30" />
          ) : cacheStats ? (
            <div className="space-y-1 text-xs text-sidebar-foreground/70">
              <div className="flex justify-between"><span>Entries</span><span className="font-semibold text-sidebar-foreground">{cacheStats.total_entries}</span></div>
              <div className="flex justify-between"><span>Total Hits</span><span className="font-semibold text-sidebar-foreground">{cacheStats.total_hits}</span></div>
            </div>
          ) : (
            <p className="text-xs text-sidebar-foreground/40">Unavailable</p>
          )}
        </div>
      )}

      {/* Health */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50 mb-2">Health</p>
          {healthLoading ? (
            <Loader2 className="w-3 h-3 animate-spin text-sidebar-foreground/50" />
          ) : health ? (
            <div className="space-y-1 text-xs text-sidebar-foreground/70">
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${health.status === "healthy" ? "bg-success" : "bg-danger"}`} />
                <span>{health.status}</span>
              </div>
              <div className="flex justify-between"><span>KB</span><span>{health.kb_loaded ? "✓ Loaded" : "✗ Not loaded"}</span></div>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-danger">
              <span className="w-2 h-2 rounded-full bg-danger" />
              <span>Offline</span>
            </div>
          )}
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center py-3 border-t border-sidebar-border hover:bg-sidebar-accent/50 transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </aside>
  );
}
