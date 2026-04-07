import { AlertCircle, Clock, CheckCircle, BarChart3 } from "lucide-react";
import type { TicketStats } from "@/lib/types";

interface KPICardsProps {
  stats: TicketStats;
}

export function KPICards({ stats }: KPICardsProps) {
  const cards = [
    { label: "Open", value: stats.open, icon: AlertCircle, color: "text-warning", bg: "bg-warning/10" },
    { label: "In Progress", value: stats.in_progress, icon: Clock, color: "text-info", bg: "bg-info/10" },
    { label: "Resolved", value: stats.resolved, icon: CheckCircle, color: "text-success", bg: "bg-success/10" },
    { label: "Total", value: stats.total, icon: BarChart3, color: "text-primary", bg: "bg-primary/10" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="bg-card rounded-xl border border-border p-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-muted-foreground">{card.label}</span>
            <div className={`w-9 h-9 rounded-lg ${card.bg} flex items-center justify-center`}>
              <card.icon className={`w-5 h-5 ${card.color}`} />
            </div>
          </div>
          <p className="text-3xl font-bold">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
