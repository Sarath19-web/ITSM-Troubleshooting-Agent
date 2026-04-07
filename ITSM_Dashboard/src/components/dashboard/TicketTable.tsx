import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { listTickets, updateTicket, getTicketStats as fetchStats } from "@/lib/api";
import type { Ticket } from "@/lib/types";
import { PriorityChip, StatusChip } from "@/components/shared/StatusChips";
import { Skeleton } from "@/components/ui/skeleton";

export function TicketTable() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [noteInput, setNoteInput] = useState("");

  const filters: Record<string, string> = {};
  if (statusFilter) filters.status = statusFilter;
  if (priorityFilter) filters.priority = priorityFilter;
  if (categoryFilter) filters.category = categoryFilter;

  const { data: tickets, isLoading, isError, refetch } = useQuery({
    queryKey: ["tickets", filters],
    queryFn: () => listTickets(Object.keys(filters).length > 0 ? filters : undefined),
  });

  // Get stats for dynamic filter options
  const { data: stats } = useQuery({
    queryKey: ["ticket-stats"],
    queryFn: fetchStats,
    refetchInterval: 10_000,
  });

  const mutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Ticket> }) => updateTicket(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["ticket-stats"] });
    },
  });

  const statusOptions = stats?.by_status ? Object.keys(stats.by_status) : [];
  const priorityOptions = stats?.by_priority ? Object.keys(stats.by_priority) : [];
  const categoryOptions = stats?.by_category ? Object.keys(stats.by_category) : [];

  if (isLoading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 text-center">
        <p className="text-sm text-muted-foreground">Failed to load tickets</p>
        <button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button>
      </div>
    );
  }

  const ticketList = tickets || [];

  return (
    <div className="bg-card rounded-xl border border-border">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 px-6 py-4 border-b border-border">
        <h3 className="text-sm font-semibold">Ticket List</h3>
        <div className="flex gap-2 flex-wrap">
          <select className="text-xs bg-background border border-input rounded-lg px-2 py-1.5" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="text-xs bg-background border border-input rounded-lg px-2 py-1.5" value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="">All Priority</option>
            {priorityOptions.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="text-xs bg-background border border-input rounded-lg px-2 py-1.5" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="">All Categories</option>
            {categoryOptions.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-6 py-3 font-medium">Ticket ID</th>
              <th className="px-6 py-3 font-medium">Summary</th>
              <th className="px-6 py-3 font-medium">Priority</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Category</th>
              <th className="px-6 py-3 font-medium">Assigned</th>
              <th className="px-6 py-3 font-medium">Created</th>
              <th className="px-6 py-3 font-medium w-8"></th>
            </tr>
          </thead>
          <tbody>
            {ticketList.map((ticket) => (
              <TicketRow
                key={ticket.ticket_id}
                ticket={ticket}
                expanded={expandedId === ticket.ticket_id}
                onToggle={() => setExpandedId(expandedId === ticket.ticket_id ? null : ticket.ticket_id)}
                noteInput={expandedId === ticket.ticket_id ? noteInput : ""}
                onNoteChange={setNoteInput}
                onUpdate={(data) => mutation.mutate({ id: ticket.ticket_id, data })}
                isUpdating={mutation.isPending}
              />
            ))}
            {ticketList.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center text-muted-foreground">No tickets found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TicketRow({
  ticket,
  expanded,
  onToggle,
  noteInput,
  onNoteChange,
  onUpdate,
  isUpdating,
}: {
  ticket: Ticket;
  expanded: boolean;
  onToggle: () => void;
  noteInput: string;
  onNoteChange: (v: string) => void;
  onUpdate: (data: Partial<Ticket>) => void;
  isUpdating: boolean;
}) {
  return (
    <>
      <tr className="border-b border-border hover:bg-accent/30 cursor-pointer transition-colors" onClick={onToggle}>
        <td className="px-6 py-3 font-mono font-semibold text-primary">{ticket.ticket_id}</td>
        <td className="px-6 py-3 max-w-[200px] truncate">{ticket.summary}</td>
        <td className="px-6 py-3"><PriorityChip priority={ticket.priority} /></td>
        <td className="px-6 py-3"><StatusChip status={ticket.status} /></td>
        <td className="px-6 py-3">{ticket.category}</td>
        <td className="px-6 py-3 max-w-[120px] truncate">{ticket.assigned_to}</td>
        <td className="px-6 py-3 text-muted-foreground">{ticket.created_at ? formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true }) : "—"}</td>
        <td className="px-6 py-3">{expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}</td>
      </tr>
      {expanded && (
        <tr className="border-b border-border bg-accent/10">
          <td colSpan={8} className="px-6 py-4">
            <div className="space-y-3 max-w-2xl">
              {ticket.description && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
                  <p className="text-sm">{ticket.description}</p>
                </div>
              )}
              {ticket.conversation_summary && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Conversation Summary</p>
                  <p className="text-sm">{ticket.conversation_summary}</p>
                </div>
              )}
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Add Note</p>
                <div className="flex gap-2">
                  <input
                    className="flex-1 bg-background border border-input rounded-lg px-3 py-1.5 text-sm"
                    placeholder="Add a note..."
                    value={noteInput}
                    onChange={(e) => onNoteChange(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <button
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    disabled={isUpdating}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (noteInput.trim()) {
                        onUpdate({ notes: [...(Array.isArray(ticket.notes) ? ticket.notes : []), { text: noteInput, timestamp: new Date().toISOString() }] as Ticket["notes"] });
                        onNoteChange("");
                      }
                    }}
                  >
                    {isUpdating ? <Loader2 className="w-3 h-3 animate-spin" /> : "Add"}
                  </button>
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                {ticket.status !== "In Progress" && (
                  <button disabled={isUpdating} onClick={(e) => { e.stopPropagation(); onUpdate({ status: "In Progress" }); }} className="px-3 py-1.5 text-xs font-medium rounded-lg bg-info/15 text-info hover:bg-info/25 transition-colors disabled:opacity-50">
                    In Progress
                  </button>
                )}
                {ticket.status !== "Resolved" && (
                  <button disabled={isUpdating} onClick={(e) => { e.stopPropagation(); onUpdate({ status: "Resolved" }); }} className="px-3 py-1.5 text-xs font-medium rounded-lg bg-success/15 text-success hover:bg-success/25 transition-colors disabled:opacity-50">
                    Resolved
                  </button>
                )}
                {ticket.status !== "Closed" && (
                  <button disabled={isUpdating} onClick={(e) => { e.stopPropagation(); onUpdate({ status: "Closed" }); }} className="px-3 py-1.5 text-xs font-medium rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 transition-colors disabled:opacity-50">
                    Closed
                  </button>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
