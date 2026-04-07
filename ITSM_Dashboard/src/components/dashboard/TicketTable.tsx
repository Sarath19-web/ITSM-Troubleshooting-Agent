import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { Ticket } from "@/lib/types";
import { PriorityChip, StatusChip } from "@/components/shared/StatusChips";

interface TicketTableProps {
  tickets: Ticket[];
  onUpdateTicket?: (id: string, data: Partial<Ticket>) => void;
}

const STATUS_OPTIONS = ["", "Open", "In Progress", "Resolved", "Closed"];
const PRIORITY_OPTIONS = ["", "P1", "P2", "P3", "P4"];
const CATEGORY_OPTIONS = ["", "Network & VPN", "Email & Calendar", "Account & Access", "Hardware", "Software Installation", "Printing", "Security"];

export function TicketTable({ tickets, onUpdateTicket }: TicketTableProps) {
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [noteInput, setNoteInput] = useState("");

  const filtered = (Array.isArray(tickets) ? tickets : []).filter((t) => {
    if (statusFilter && t.status !== statusFilter) return false;
    if (priorityFilter && t.priority !== priorityFilter) return false;
    if (categoryFilter && t.category !== categoryFilter) return false;
    return true;
  });

  return (
    <div className="bg-card rounded-xl border border-border">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 px-6 py-4 border-b border-border">
        <h3 className="text-sm font-semibold">Ticket List</h3>
        <div className="flex gap-2 flex-wrap">
          <select className="text-xs bg-background border border-input rounded-lg px-2 py-1.5" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            {STATUS_OPTIONS.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="text-xs bg-background border border-input rounded-lg px-2 py-1.5" value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="">All Priority</option>
            {PRIORITY_OPTIONS.filter(Boolean).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="text-xs bg-background border border-input rounded-lg px-2 py-1.5" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="">All Categories</option>
            {CATEGORY_OPTIONS.filter(Boolean).map((c) => <option key={c} value={c}>{c}</option>)}
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
            {filtered.map((ticket) => (
              <>
                <tr
                  key={ticket.ticket_id}
                  className="border-b border-border hover:bg-accent/30 cursor-pointer transition-colors"
                  onClick={() => setExpandedId(expandedId === ticket.ticket_id ? null : ticket.ticket_id)}
                >
                  <td className="px-6 py-3 font-mono font-semibold text-primary">{ticket.ticket_id}</td>
                  <td className="px-6 py-3 max-w-[200px] truncate">{ticket.summary}</td>
                  <td className="px-6 py-3"><PriorityChip priority={ticket.priority} /></td>
                  <td className="px-6 py-3"><StatusChip status={ticket.status} /></td>
                  <td className="px-6 py-3">{ticket.category}</td>
                  <td className="px-6 py-3 max-w-[120px] truncate">{ticket.assigned_to}</td>
                  <td className="px-6 py-3 text-muted-foreground">{ticket.created_at ? formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true }) : "—"}</td>
                  <td className="px-6 py-3">{expandedId === ticket.ticket_id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}</td>
                </tr>
                {expandedId === ticket.ticket_id && (
                  <tr key={`${ticket.ticket_id}-detail`} className="border-b border-border bg-accent/10">
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
                              onChange={(e) => setNoteInput(e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                            />
                            <button
                              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (noteInput.trim()) {
                                  onUpdateTicket?.(ticket.ticket_id, { notes: [...(ticket.notes || []), noteInput] });
                                  setNoteInput("");
                                }
                              }}
                            >
                              Add
                            </button>
                          </div>
                        </div>
                        <div className="flex gap-2 pt-2">
                          {ticket.status !== "In Progress" && (
                            <button onClick={(e) => { e.stopPropagation(); onUpdateTicket?.(ticket.ticket_id, { status: "In Progress" }); }} className="px-3 py-1.5 text-xs font-medium rounded-lg bg-info/15 text-info hover:bg-info/25 transition-colors">
                              In Progress
                            </button>
                          )}
                          {ticket.status !== "Resolved" && (
                            <button onClick={(e) => { e.stopPropagation(); onUpdateTicket?.(ticket.ticket_id, { status: "Resolved" }); }} className="px-3 py-1.5 text-xs font-medium rounded-lg bg-success/15 text-success hover:bg-success/25 transition-colors">
                              Resolved
                            </button>
                          )}
                          {ticket.status !== "Closed" && (
                            <button onClick={(e) => { e.stopPropagation(); onUpdateTicket?.(ticket.ticket_id, { status: "Closed" }); }} className="px-3 py-1.5 text-xs font-medium rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 transition-colors">
                              Closed
                            </button>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
            {filtered.length === 0 && (
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
