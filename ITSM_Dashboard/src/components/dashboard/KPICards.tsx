import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Clock, CheckCircle, BarChart3 } from "lucide-react";
import { getTicketStats } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export function KPICards() {
  const { data: stats, isLoading, isError, refetch } = useQuery({
    queryKey: ["ticket-stats"],
    queryFn: getTicketStats,
    refetchInterval: 10_000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card rounded-xl border border-border p-6">
            <Skeleton className="h-4 w-20 mb-3" />
            <Skeleton className="h-8 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 text-center">
        <p className="text-sm text-muted-foreground">Failed to load stats</p>
        <button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button>
      </div>
    );
  }

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
