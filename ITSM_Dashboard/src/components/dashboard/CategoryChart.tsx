import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { getTicketStats } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

const COLORS = ["#346739", "#79AE6F", "#FF8B5A", "#4A90D9", "#FD7979", "#9CA3AF", "#6B7280"];

export function CategoryChart() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["ticket-stats"],
    queryFn: getTicketStats,
    refetchInterval: 10_000,
  });

  const chartData = Object.entries(stats?.by_category || {}).map(([name, value]) => ({ name, value }));

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
      <h3 className="text-sm font-semibold mb-4">Tickets by Category</h3>
      {chartData.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-12">No category data available</p>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
            <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid var(--border)", fontSize: 12 }} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
