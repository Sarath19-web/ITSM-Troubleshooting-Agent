import { useEffect, useRef, useCallback } from "react";

const WS_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .replace(/^http/, "ws");

interface WSMessage {
  type: "new_message";
  message: {
    role: "user" | "agent";
    content: string;
    timestamp: string;
    metadata?: Record<string, unknown>;
  };
}

/**
 * Subscribe to real-time messages for a session via WebSocket.
 * Calls `onMessage` whenever a new message arrives.
 * Reconnects automatically on disconnect.
 */
export type { WSMessage };

export function useSessionWS(
  sessionId: string | null | undefined,
  onMessage: (msg: WSMessage) => void,
) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closingRef = useRef(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    if (!sessionId) return;
    closingRef.current = false;
    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(`${WS_BASE}/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const data: WSMessage = JSON.parse(evt.data);
        onMessageRef.current(data);
      } catch { /* ignore non-JSON */ }
    };

    ws.onclose = () => {
      if (closingRef.current) return; // intentional close, don't reconnect
      reconnectTimer.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [sessionId]);

  useEffect(() => {
    connect();
    return () => {
      closingRef.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
