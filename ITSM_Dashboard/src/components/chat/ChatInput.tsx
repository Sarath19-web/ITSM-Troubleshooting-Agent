import { useState } from "react";
import { Send, Ticket, RefreshCw, ClipboardList } from "lucide-react";
import { Link } from "@tanstack/react-router";

interface ChatInputProps {
  onSend: (message: string) => void;
  onNewChat: () => void;
  onCreateTicket: () => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, onNewChat, onCreateTicket, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed.slice(0, 2000));
    setInput("");
  };

  return (
    <div className="border-t border-border bg-card px-4 py-3 space-y-3">
      <div className="flex gap-2">
        <input
          className="flex-1 bg-background border border-input rounded-lg px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          maxLength={2000}
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          className="bg-primary text-primary-foreground rounded-lg px-4 py-2.5 hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
      {input.length > 1800 && (
        <p className="text-xs text-muted-foreground">{input.length}/2000 characters</p>
      )}
      <div className="flex gap-2">
        <button onClick={onCreateTicket} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border hover:bg-accent transition-colors">
          <Ticket className="w-3.5 h-3.5" /> Create Ticket
        </button>
        <button onClick={onNewChat} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border hover:bg-accent transition-colors">
          <RefreshCw className="w-3.5 h-3.5" /> New Chat
        </button>
        <Link to="/dashboard" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border hover:bg-accent transition-colors">
          <ClipboardList className="w-3.5 h-3.5" /> View Tickets
        </Link>
      </div>
    </div>
  );
}
