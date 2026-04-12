import { useState } from "react";
import { Send, Ticket, RefreshCw } from "lucide-react";

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
    <div className="px-4 py-3 space-y-3">
      <div className="rounded-2xl backdrop-blur-md bg-[#79AE6F]/15 border border-[#79AE6F]/30 px-4 py-4 space-y-3 shadow-lg">
        <div className="flex gap-2">
          <input
            className="flex-1 bg-white/10 border border-[#79AE6F]/40 rounded-xl px-4 py-2.5 text-sm placeholder:text-black/50 text-black focus:outline-none focus:ring-2 focus:ring-[#79AE6F]/60 transition-all"
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
            className="bg-[#79AE6F] text-black rounded-xl px-4 py-2.5 hover:bg-[#6a9b5f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        {input.length > 1800 && (
          <p className="text-xs text-black/60">{input.length}/2000 characters</p>
        )}
        <div className="flex gap-2">
          <button onClick={onCreateTicket} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-[#79AE6F]/40 hover:bg-[#79AE6F]/20 transition-colors text-black/90">
            <Ticket className="w-3.5 h-3.5" /> Create Ticket
          </button>
          <button onClick={onNewChat} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-[#79AE6F]/40 hover:bg-[#79AE6F]/20 transition-colors text-black/90">
            <RefreshCw className="w-3.5 h-3.5" /> New Chat
          </button>
        </div>
      </div>
      <div className="text-center text-xs text-black/60 px-4">
        <p>Alex is AI and can make mistakes. Please double-check responses.</p>
      </div>
    </div>
  );
}
