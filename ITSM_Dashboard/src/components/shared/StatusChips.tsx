import type { Ticket } from "@/lib/types";

export function PriorityChip({ priority }: { priority: Ticket["priority"] }) {
  const styles: Record<string, string> = {
    P1: "bg-danger/15 text-danger",
    P2: "bg-warning/15 text-warning",
    P3: "bg-info/15 text-info",
    P4: "bg-muted text-muted-foreground",
  };
  const labels: Record<string, string> = { P1: "Critical", P2: "High", P3: "Medium", P4: "Low" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${styles[priority] || styles.P4}`}>
      {priority} — {labels[priority] || "Low"}
    </span>
  );
}

export function StatusChip({ status }: { status: Ticket["status"] }) {
  const styles: Record<string, string> = {
    Open: "bg-warning/15 text-warning",
    "In Progress": "bg-info/15 text-info",
    Resolved: "bg-success/15 text-success",
    Closed: "bg-muted text-muted-foreground",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${styles[status] || styles.Open}`}>
      {status}
    </span>
  );
}
