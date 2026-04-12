import { Bot, Zap, Lightbulb, ChevronDown, ChevronRight, CheckSquare, Square, Headset } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import type { ChatMessage as ChatMessageType, Ticket } from "@/lib/types";
import { TicketBubble } from "./TicketBubble";
import { DraftTicketBubble } from "./DraftTicketBubble";

interface ChatMessageProps {
  message: ChatMessageType;
  onSubmitDraft?: (edited: Partial<Ticket>) => void;
  onCancelDraft?: () => void;
}

// Helper function to parse markdown bold (**text**) and convert to bold elements
function parseMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={idx}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

// Higher-order parser for handling check lists and text blocks
function parseMessageContent(text: string) {
  const lines = text.split('\n');
  return lines.map((line, lineIdx) => {
    const trimmed = line.trim();
    const checkedMatch = trimmed.match(/^-\s*\[x\]\s*(.*)/i);
    const uncheckedMatch = trimmed.match(/^-\s*\[ \]\s*(.*)/i);

    if (checkedMatch || uncheckedMatch) {
      const isChecked = !!checkedMatch;
      const content = checkedMatch ? checkedMatch[1] : (uncheckedMatch ? uncheckedMatch[1] : "");

      return (
        <div key={lineIdx} className="flex items-start gap-2 my-1.5">
          <div className="mt-[3px] shrink-0">
            {isChecked ? (
              <CheckSquare className="w-[14px] h-[14px] text-green-500" />
            ) : (
              <Square className="w-[14px] h-[14px] bg-foreground/10 text-foreground/40 rounded border-none" />
            )}
          </div>
          <div className="leading-relaxed">{parseMarkdownBold(content)}</div>
        </div>
      );
    }

    return (
      <span key={lineIdx}>
        {parseMarkdownBold(line)}
        {lineIdx < lines.length - 1 && <br />}
      </span>
    );
  });
}

// Extract suggestion from content (📌 *text*)
function extractSuggestion(text: string) {
  if (!text) return { mainContent: text || "", suggestion: null };
  // Match 📌 *...* at the end or on separate line, handling ** for bold inside
  const suggestionMatch = text.match(/📌\s*\*(.+?)\*\s*$/s);
  if (!suggestionMatch) {
    return { mainContent: text, suggestion: null };
  }
  const suggestion = suggestionMatch[1].trim();
  const mainContent = text.replace(/📌\s*\*.+?\*\s*$/s, "").trim();
  return { mainContent, suggestion };
}

export function ChatMessage({ message, onSubmitDraft, onCancelDraft }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isHumanAgent = message.metadata?.intent === "human_agent";
  const [expandedSuggestion, setExpandedSuggestion] = useState(false);
  const { mainContent, suggestion } = extractSuggestion(message.content);

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} mb-4`}>
      {!isUser && (
        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${
          isHumanAgent ? "bg-orange-500" : "bg-primary"
        }`}>
          {isHumanAgent ? (
            <Headset className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-primary-foreground" />
          )}
        </div>
      )}

      <div className={`max-w-[75%] space-y-2 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        {/* IT Support label */}
        {isHumanAgent && (
          <p className="text-[10px] text-orange-500 font-semibold">
            {message.metadata?.agent_name || "IT Support"}
          </p>
        )}
        <div
          className={`relative px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${isUser
              ? "bg-user-bubble text-user-bubble-foreground rounded-[16px_16px_4px_16px]"
              : isHumanAgent
              ? "bg-orange-500/10 text-foreground rounded-[16px_16px_16px_4px] border border-orange-500/20"
              : "bg-agent-bubble text-foreground rounded-[16px_16px_16px_4px]"
            }`}
        >
          {parseMessageContent(mainContent)}

          {/* Suggestion icon in bottom right of bubble */}
          {suggestion && !isUser && (
            <button
              onClick={() => setExpandedSuggestion(!expandedSuggestion)}
              className="absolute bottom-2 right-2 text-foreground/60 hover:text-foreground transition-colors"
              title="Toggle suggestion"
            >
              <Lightbulb className="w-4 h-4" />
            </button>
          )}

          {/* Expandable suggestion inside bubble */}
          {suggestion && !isUser && expandedSuggestion && (
            <div className="mt-3 pt-3 border-t border-foreground/20 text-xs text-foreground/80">
              {parseMarkdownBold(suggestion)}
            </div>
          )}
        </div>

        {/* Cache badge */}
        {message.from_cache && !isUser && (
          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-success/15 text-success font-medium">
            <Zap className="w-3 h-3" /> Cached response (instant)
          </span>
        )}

        {/* Ticket card */}
        {message.ticket && <TicketBubble ticket={message.ticket} />}
        {message.draft_ticket && <DraftTicketBubble draft={message.draft_ticket} onSubmit={onSubmitDraft} onCancel={onCancelDraft} />}

        {/* KB Sources */}
        {message.kb_sources && message.kb_sources.length > 0 && !isUser && (
          <div className="flex flex-wrap gap-1">
            {message.kb_sources.map((kb, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground font-medium">
                📚 {kb.preview.slice(0, 40)}
              </span>
            ))}
          </div>
        )}

        {/* Troubleshooting progress */}
        {message.troubleshoot_turn != null && message.max_turns && !isUser && message.troubleshoot_turn > 0 && (
          <div className="flex items-center gap-2">
            <div className="h-1 w-20 bg-border rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${(message.troubleshoot_turn / message.max_turns) * 100}%` }}
              />
            </div>
            <span className="text-[10px] text-muted-foreground">
              Turn {message.troubleshoot_turn}/{message.max_turns}
              {message.troubleshoot_turn >= message.max_turns && " — Escalation recommended"}
            </span>
          </div>
        )}

        {/* Timestamp */}
        <span className={`text-[10px] text-muted-foreground ${isUser ? "text-right" : "text-left"}`}>
          {formatDistanceToNow(message.timestamp, { addSuffix: true })}
        </span>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-4">
      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
        <Bot className="w-4 h-4 text-primary-foreground" />
      </div>
      <div className="bg-agent-bubble rounded-[16px_16px_16px_4px] px-4 py-3 flex items-center gap-1.5">
        <span className="typing-dot w-2 h-2 rounded-full bg-muted-foreground/50" />
        <span className="typing-dot w-2 h-2 rounded-full bg-muted-foreground/50" />
        <span className="typing-dot w-2 h-2 rounded-full bg-muted-foreground/50" />
      </div>
    </div>
  );
}
