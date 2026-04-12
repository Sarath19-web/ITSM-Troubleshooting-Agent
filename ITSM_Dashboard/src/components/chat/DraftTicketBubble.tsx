import { useState } from "react";
import { Edit3, Send, X, ChevronDown } from "lucide-react";
import type { Ticket } from "@/lib/types";
import { PriorityChip } from "@/components/shared/StatusChips";

interface DraftTicketBubbleProps {
  draft: Partial<Ticket>;
  onSubmit?: (edited: Partial<Ticket>) => void;
  onCancel?: () => void;
}

const PRIORITY_OPTIONS = [
  { value: "P1", label: "P1 — Critical" },
  { value: "P2", label: "P2 — High" },
  { value: "P3", label: "P3 — Medium" },
  { value: "P4", label: "P4 — Low" },
];

export function DraftTicketBubble({ draft, onSubmit, onCancel }: DraftTicketBubbleProps) {
  const [summary, setSummary] = useState(draft.summary || "");
  const [description, setDescription] = useState(draft.description || "");
  const [priority, setPriority] = useState(draft.priority || "P3");
  const [category] = useState(draft.category || "Other");
  const [isEditing, setIsEditing] = useState(false);

  const handleSubmit = () => {
    onSubmit?.({ ...draft, summary, description, priority, category });
  };

  const handleCancel = () => {
    onCancel?.();
  };

  return (
    <div className="w-full bg-amber-500/10 border-l-4 border-amber-500 rounded-lg p-4 space-y-3 mt-2 mb-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Edit3 className="w-4 h-4 text-amber-600" />
          <span className="text-sm font-semibold text-amber-600">
            Ticket Draft — Pending Review
          </span>
        </div>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="text-xs text-amber-600 hover:text-amber-700 underline underline-offset-2 transition-colors"
        >
          {isEditing ? "Done Editing" : "Edit Fields"}
        </button>
      </div>

      {/* Fields */}
      <div className="grid grid-cols-1 gap-3 text-sm">
        {/* Summary */}
        <div>
          <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
            Summary
          </span>
          {isEditing ? (
            <input
              type="text"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full mt-1 px-2 py-1.5 text-sm rounded-md border border-amber-300 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          ) : (
            <p className="font-medium text-foreground">{summary || "N/A"}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
            Description
          </span>
          {isEditing ? (
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full mt-1 px-2 py-1.5 text-sm rounded-md border border-amber-300 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-amber-400 resize-y"
            />
          ) : (
            <p className="text-foreground whitespace-pre-wrap">{description || "N/A"}</p>
          )}
        </div>

        {/* Priority & Category row */}
        <div className="grid grid-cols-2 gap-2 mt-1">
          <div>
            <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
              Priority
            </span>
            {isEditing ? (
              <div className="relative mt-1">
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as any)}
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-amber-300 bg-background text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-amber-400"
                >
                  {PRIORITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
              </div>
            ) : (
              <div className="mt-0.5">
                <PriorityChip priority={priority as any} />
              </div>
            )}
          </div>
          <div>
            <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
              Category
            </span>
            <p className="font-medium mt-0.5">{category}</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2 pt-2 border-t border-amber-300/30">
        <button
          onClick={handleSubmit}
          className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors"
        >
          <Send className="w-3.5 h-3.5" />
          Submit Ticket
        </button>
        <button
          onClick={handleCancel}
          className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors"
        >
          <X className="w-3.5 h-3.5" />
          Cancel
        </button>
      </div>
    </div>
  );
}
