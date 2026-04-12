"""
Session persistence service.
Persists conversation history and session state to disk so sessions
survive server restarts and can be retrieved later for audit/replay.
"""
import json
import os
import threading
from datetime import datetime
from pathlib import Path

from app.services.logger import get_logger

logger = get_logger("session_store")

SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = SESSIONS_DIR / "_index.json"

_lock = threading.Lock()


def _session_file(session_id):
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")
    return SESSIONS_DIR / f"{safe}.json"


def save_session(session):
    """Persist a session to disk."""
    try:
        data = {
            "session_id": session.session_id,
            "user_name": session.user_name,
            "current_category": session.current_category,
            "original_issue": getattr(session, "original_issue", None),
            "troubleshoot_turn": session.troubleshoot_turn,
            "steps_completed": session.steps_completed,
            "failed_steps": session.failed_steps,
            "deferred_intents": session.deferred_intents,
            "clarifying_questions_asked": session.clarifying_questions_asked,
            "ticket_created": session.ticket_created,
            "history": session.history,
            "created_at": getattr(session, "created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat(),
        }
        with _lock:
            with open(_session_file(session.session_id), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            _update_index(session.session_id, data)
        logger.debug(f"Saved session {session.session_id} ({len(session.history)} messages)")
    except Exception as e:
        logger.error(f"Failed to save session {session.session_id}: {e}")


def load_session(session_id):
    """Load session data from disk. Returns dict or None."""
    try:
        path = _session_file(session_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load session {session_id}: {e}")
        return None


def list_sessions(limit=50, user_name=None):
    """List all persisted sessions, newest first."""
    if not INDEX_FILE.exists():
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index = json.load(f)
        sessions = list(index.values())
        if user_name:
            sessions = [s for s in sessions if s.get("user_name") == user_name]
        sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        return sessions[:limit]
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return []


def delete_session(session_id):
    try:
        path = _session_file(session_id)
        if path.exists():
            path.unlink()
        with _lock:
            if INDEX_FILE.exists():
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    index = json.load(f)
                index.pop(session_id, None)
                with open(INDEX_FILE, "w", encoding="utf-8") as f:
                    json.dump(index, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        return False


def _update_index(session_id, data):
    """Update the session index with summary info."""
    try:
        if INDEX_FILE.exists():
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {}

        first_user_msg = ""
        for h in data.get("history", []):
            if h.get("role") == "user":
                first_user_msg = h.get("content", "")[:80]
                break

        index[session_id] = {
            "session_id": session_id,
            "user_name": data.get("user_name"),
            "label": first_user_msg or "New conversation",
            "category": data.get("current_category"),
            "message_count": len(data.get("history", [])),
            "ticket_created": data.get("ticket_created", {}).get("ticket_id") if data.get("ticket_created") else None,
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to update session index: {e}")


def restore_into_session_object(session, data):
    """Hydrate an in-memory ITSMSession from a dict loaded from disk."""
    session.user_name = data.get("user_name")
    session.current_category = data.get("current_category")
    session.original_issue = data.get("original_issue")
    session.troubleshoot_turn = data.get("troubleshoot_turn", 0)
    session.steps_completed = data.get("steps_completed", [])
    session.failed_steps = data.get("failed_steps", [])
    session.deferred_intents = data.get("deferred_intents", [])
    session.clarifying_questions_asked = data.get("clarifying_questions_asked", 0)
    session.ticket_created = data.get("ticket_created")
    session.history = data.get("history", [])
    session.created_at = data.get("created_at")
    return session