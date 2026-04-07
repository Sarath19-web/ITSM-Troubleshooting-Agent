import { useState } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { MessageSquare, LayoutDashboard, Settings, ChevronLeft, ChevronRight, Bot } from "lucide-react";
import type { Session } from "@/lib/types";

interface AppSidebarProps {
  sessions?: Session[];
  openTickets?: number;
  avgResponseTime?: string;
  baseUrl?: string;
  onBaseUrlChange?: (url: string) => void;
}

export function AppSidebar({ sessions = [], openTickets = 0, avgResponseTime = "—", baseUrl = "", onBaseUrlChange }: AppSidebarProps) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [editingUrl, setEditingUrl] = useState(false);
  const [urlInput, setUrlInput] = useState(baseUrl);

  const navItems = [
    { label: "Chat", to: "/", icon: MessageSquare },
    { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  ];

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
      <nav className="flex-1 px-2 py-4 space-y-1">
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

      {/* Quick Stats */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50 mb-2">Quick Stats</p>
          <div className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-sidebar-foreground/70">Open Tickets</span>
              <span className="font-semibold text-warning">{openTickets}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sidebar-foreground/70">Avg Response</span>
              <span className="font-semibold">{avgResponseTime}</span>
            </div>
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      {!collapsed && sessions.length > 0 && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50 mb-2">Recent Sessions</p>
          <div className="space-y-1">
            {sessions.slice(0, 3).map((s) => (
              <div key={s.id} className="text-sm text-sidebar-foreground/70 truncate">
                • {s.label} ({s.messageCount} msgs)
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <div className="flex items-center gap-2 text-sm text-sidebar-foreground/70 mb-1">
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </div>
          <div className="text-xs text-sidebar-foreground/50">
            {editingUrl ? (
              <input
                className="w-full bg-sidebar-accent text-sidebar-foreground px-2 py-1 rounded text-xs font-mono"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onBlur={() => { onBaseUrlChange?.(urlInput); setEditingUrl(false); }}
                onKeyDown={(e) => { if (e.key === "Enter") { onBaseUrlChange?.(urlInput); setEditingUrl(false); } }}
                autoFocus
              />
            ) : (
              <button onClick={() => setEditingUrl(true)} className="hover:text-sidebar-foreground transition-colors font-mono truncate block w-full text-left">
                API: {baseUrl}
              </button>
            )}
          </div>
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
