import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

const PRIORITY_COLORS: Record<string, string> = { P1: "#FD7979", P2: "#FF8B5A", P3: "#4A90D9", P4: "#9CA3AF" };

interface PriorityChartProps {
  data: Record<string, number>;
}

export function PriorityChart({ data }: PriorityChartProps) {
  const chartData = Object.entries(data || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <h3 className="text-sm font-semibold mb-4">Tickets by Priority</h3>
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
    </div>
  );
}
