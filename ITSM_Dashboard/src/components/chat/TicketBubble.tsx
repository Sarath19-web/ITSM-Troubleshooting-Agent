import { Link } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";
import type { Ticket } from "@/lib/types";
import { PriorityChip } from "@/components/shared/StatusChips";

interface TicketBubbleProps {
  ticket: Ticket;
}

export function TicketBubble({ ticket }: TicketBubbleProps) {
  return (
    <div className="w-full bg-ticket-bg border-l-4 border-primary rounded-lg p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-primary">Ticket Created</span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-muted-foreground text-xs">Ticket ID</span>
          <p className="font-mono font-semibold">{ticket.ticket_id}</p>
        </div>
        <div>
          <span className="text-muted-foreground text-xs">Priority</span>
          <div className="mt-0.5"><PriorityChip priority={ticket.priority} /></div>
        </div>
        <div>
          <span className="text-muted-foreground text-xs">Category</span>
          <p className="font-medium">{ticket.category}</p>
        </div>
        <div>
          <span className="text-muted-foreground text-xs">Assigned to</span>
          <p className="font-medium">{ticket.assigned_to}</p>
        </div>
      </div>
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline mt-1"
      >
        View Ticket <ExternalLink className="w-3 h-3" />
      </Link>
    </div>
  );
}
