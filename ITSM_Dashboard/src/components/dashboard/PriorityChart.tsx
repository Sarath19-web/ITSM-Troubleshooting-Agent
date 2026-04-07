import { useQuery } from "@tanstack/react-query";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { getTicketStats } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

const PRIORITY_COLORS: Record<string, string> = { P1: "#FD7979", P2: "#FF8B5A", P3: "#4A90D9", P4: "#9CA3AF" };

export function PriorityChart() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["ticket-stats"],
    queryFn: getTicketStats,
    refetchInterval: 10_000,
  });

  const chartData = Object.entries(stats?.by_priority || {}).map(([name, value]) => ({ name, value }));

  if (isLoading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <Skeleton className="h-4 w-40 mb-4" />
        <Skeleton className="h-[250px] w-full" />
      </div>
    );
  }

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <h3 className="text-sm font-semibold mb-4">Tickets by Priority</h3>
      {chartData.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-12">No priority data available</p>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={chartData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value" nameKey="name">
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name] || "#9CA3AF"} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid var(--border)", fontSize: 12 }} />
            <Legend formatter={(value: string) => <span className="text-xs">{value}</span>} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
