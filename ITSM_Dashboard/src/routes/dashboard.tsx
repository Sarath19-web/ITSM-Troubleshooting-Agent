import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import { useApi } from "@/lib/api-context";
import type { Ticket, TicketStats } from "@/lib/types";
import { AppSidebar } from "@/components/AppSidebar";
import { KPICards } from "@/components/dashboard/KPICards";
import { CategoryChart } from "@/components/dashboard/CategoryChart";
import { PriorityChart } from "@/components/dashboard/PriorityChart";
import { TicketTable } from "@/components/dashboard/TicketTable";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
});

function DashboardPage() {
  const api = useApi();
  const [stats, setStats] = useState<TicketStats>({ open: 0, in_progress: 0, resolved: 0, total: 0, by_category: {}, by_priority: {} });
  const [tickets, setTickets] = useState<Ticket[]>([]);

  useEffect(() => {
    api.getTicketStats().then(setStats);
    api.getTickets().then(setTickets);
  }, [api]);

  const handleUpdateTicket = useCallback(async (id: string, data: Partial<Ticket>) => {
    const updated = await api.updateTicket(id, data);
    setTickets((prev) => prev.map((t) => (t.ticket_id === id ? { ...t, ...updated } : t)));
  }, [api]);

  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar openTickets={stats.open} avgResponseTime="4.2s" baseUrl={api.baseUrl} onBaseUrlChange={api.setBaseUrl} />
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6 max-w-[1400px]">
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <KPICards stats={stats} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <CategoryChart data={stats.by_category} />
            <PriorityChart data={stats.by_priority} />
          </div>
          <TicketTable tickets={tickets} onUpdateTicket={handleUpdateTicket} />
        </div>
      </main>
    </div>
  );
}
