"""WebSocket connection manager for real-time session messaging."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger("ws_manager")


class ConnectionManager:
    """Manages WebSocket connections grouped by session_id."""

    def __init__(self):
        # session_id -> set of connected websockets
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        if session_id not in self._connections:
            self._connections[session_id] = set()
        self._connections[session_id].add(ws)
        logger.info(f"WS connect: session={session_id}, total={len(self._connections[session_id])}")

    def disconnect(self, ws: WebSocket, session_id: str):
        if session_id in self._connections:
            self._connections[session_id].discard(ws)
            remaining = len(self._connections[session_id])
            if not self._connections[session_id]:
                del self._connections[session_id]
            logger.info(f"WS disconnect: session={session_id}, remaining={remaining}")

    async def broadcast(self, session_id: str, message: dict):
        """Send a JSON message to all connections subscribed to a session."""
        sockets = self._connections.get(session_id, set()).copy()
        logger.info(f"WS broadcast: session={session_id}, recipients={len(sockets)}, type={message.get('type')}")
        payload = json.dumps(message, default=str)
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"WS send failed: session={session_id}, error={e}")
                self.disconnect(ws, session_id)


ws_manager = ConnectionManager()
