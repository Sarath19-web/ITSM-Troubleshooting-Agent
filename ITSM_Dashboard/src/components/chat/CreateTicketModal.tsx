import { useState } from "react";
import { X } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface CreateTicketModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { summary: string; category: string; priority: string; description: string }) => void;
  categories?: string[];
}

export function CreateTicketModal({ open, onClose, onSubmit, categories }: CreateTicketModalProps) {
  const [summary, setSummary] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("P2");
  const [description, setDescription] = useState("");

  if (!open) return null;

  const cats = Array.isArray(categories) ? categories : [];

  const handleSubmit = () => {
    if (!summary.trim()) return;
    onSubmit({ summary, category: category || cats[0] || "General", priority, description });
    setSummary("");
    setDescription("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-card rounded-xl shadow-2xl w-full max-w-lg mx-4 border border-border" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold">Create Support Ticket</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Summary *</label>
            <input
              className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="Brief description of the issue"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Category</label>
              {cats.length === 0 ? (
                <Skeleton className="h-9 w-full" />
              ) : (
                <select
                  className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  value={category || cats[0]}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {cats.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Priority</label>
              <select
                className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="P1">P1 — Critical</option>
                <option value="P2">P2 — High</option>
                <option value="P3">P3 — Medium</option>
                <option value="P4">P4 — Low</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Description</label>
            <textarea
              className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px] resize-y"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed description of the issue..."
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-border">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium rounded-lg border border-border hover:bg-accent transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!summary.trim()}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            Create Ticket
          </button>
        </div>
      </div>
    </div>
  );
}
