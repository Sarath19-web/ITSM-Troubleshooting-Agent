import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.engine import (
    process_message, create_ticket_direct, get_session,
    reset_session, warmup, _sessions,
)
from app.services.tickets import ticket_service
from app.services.session_store import (
    list_sessions, load_session, delete_session, save_session,
)
from app.services.faq_cache import faq_cache
from app.services.logger import setup_logging, get_logger, log_access, PIPELINE_LOG, ACCESS_LOG, ERROR_LOG
from app.config import TICKET_CATEGORIES, TICKET_PRIORITIES, MAX_TROUBLESHOOT_TURNS

setup_logging()
logger = get_logger("api")

app = FastAPI(title="ITSM Troubleshooting Agent API", version="1.1")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every API request with duration."""
    start = time.time()
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        log_access(request.method, request.url.path, response.status_code, duration_ms)
        if duration_ms > 5000:
            logger.warning(f"SLOW {request.method} {request.url.path} {duration_ms:.0f}ms")
        return response
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        logger.error(f"Request failed: {request.method} {request.url.path} → {e}", exc_info=True)
        log_access(request.method, request.url.path, 500, duration_ms, extra={"error": str(e)})
        raise


@app.on_event("startup")
async def startup():
    logger.info("FastAPI startup event triggered")
    warmup()


@app.on_event("shutdown")
async def shutdown():
    logger.info("FastAPI shutdown — saving all in-memory sessions")
    for session in _sessions.values():
        try:
            save_session(session)
        except Exception as e:
            logger.error(f"Failed to save session on shutdown: {e}")


# ──────────────────────────────────────────────────────────────────
# Request models
# ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = "default"
    user_name: Optional[str] = None

class TicketRequest(BaseModel):
    session_id: Optional[str] = "default"
    summary: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = "Other"
    priority: Optional[str] = "P3"
    description: Optional[str] = None
    user_name: Optional[str] = None

class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None

class ResetRequest(BaseModel):
    session_id: Optional[str] = "default"


# ──────────────────────────────────────────────────────────────────
# Health & meta
# ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    import os
    from app.config import DB_PATH
    return {
        "status": "healthy" if os.path.exists(DB_PATH) else "degraded",
        "agent": "ITSM Troubleshooting Agent v1.1",
        "kb_loaded": os.path.exists(DB_PATH),
        "active_sessions": len(_sessions),
        "cache_entries": faq_cache.stats()["total_entries"],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/categories")
def categories():
    return {"categories": TICKET_CATEGORIES, "priorities": TICKET_PRIORITIES,
            "max_troubleshoot_turns": MAX_TROUBLESHOOT_TURNS}


# ──────────────────────────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(req: ChatRequest):
    result = process_message(req.message, req.session_id, req.user_name)
    if not result:
        raise HTTPException(500, "Agent failed to process message.")
    return {
        "reply": result["response"],
        "session_id": result["session_id"],
        "intent": result["intent"],
        "category": result["category"],
        "troubleshoot_turn": result["troubleshoot_turn"],
        "max_turns": result["max_turns"],
        "deferred_intents": result.get("deferred_intents", []),
        "steps_completed": result.get("steps_completed", []),
        "failed_steps": result.get("failed_steps", []),
        "ticket": result["ticket"],
        "draft_ticket": result.get("draft_ticket", None),
        "response_time_ms": result["response_time_ms"],
        "kb_sources": result["kb_sources"],
        "from_cache": result.get("from_cache", False),
        "cache_type": result.get("cache_type"),
    }


# ──────────────────────────────────────────────────────────────────
# Tickets
# ──────────────────────────────────────────────────────────────────

@app.post("/tickets")
def create_ticket(req: TicketRequest):
    ticket = create_ticket_direct(
        session_id=req.session_id, summary=req.summary,
        category=req.category, priority=req.priority,
        description=req.description, user_name=req.user_name,
    )
    # Clear draft state and persist ticket to session history
    if req.session_id and req.session_id in _sessions:
        session = _sessions[req.session_id]
        session.draft_ticket = None
        session.awaiting_ticket_confirmation = False
        session.ticket_created = ticket
        # Persist ticket creation message so it shows in history on reload
        session.add_message("agent", "Your ticket has been submitted successfully! 🎉", {
            "intent": "ticket_created",
            "ticket_created": ticket["ticket_id"],
        })
        save_session(session)
    return {"status": "created", "ticket": ticket}


@app.get("/tickets")
def list_tickets(status: Optional[str] = None, priority: Optional[str] = None,
                 category: Optional[str] = None):
    tickets = ticket_service.get_all_tickets(status, priority, category)
    return {"tickets": tickets, "count": len(tickets)}


@app.get("/tickets/stats")
def ticket_stats():
    return ticket_service.get_stats()


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = ticket_service.get_ticket(ticket_id.upper())
    if not ticket:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    return ticket


@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, req: TicketUpdateRequest):
    updates = {}
    if req.status:
        updates["status"] = req.status
    if req.priority:
        updates["priority"] = req.priority
        updates["priority_label"] = TICKET_PRIORITIES.get(req.priority, "Medium")
    if req.notes:
        ticket = ticket_service.get_ticket(ticket_id.upper())
        if ticket:
            notes = ticket.get("notes", [])
            notes.append({"text": req.notes, "timestamp": datetime.utcnow().isoformat()})
            updates["notes"] = notes
    result = ticket_service.update_ticket(ticket_id.upper(), updates)
    if not result:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    return {"status": "updated", "ticket": result}


# ──────────────────────────────────────────────────────────────────
# Sessions (with persistence)
# ──────────────────────────────────────────────────────────────────

@app.get("/sessions")
def get_all_sessions(limit: int = 50, user_name: Optional[str] = None):
    """List all persisted sessions for the sidebar history."""
    return {"sessions": list_sessions(limit=limit, user_name=user_name)}


@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    """Get full session detail including history."""
    if session_id in _sessions:
        session = _sessions[session_id]
        return {
            "session_id": session.session_id,
            "user_name": session.user_name,
            "message_count": len(session.history),
            "troubleshoot_turn": session.troubleshoot_turn,
            "max_turns": MAX_TROUBLESHOOT_TURNS,
            "current_category": session.current_category,
            "steps_completed": session.steps_completed,
            "failed_steps": session.failed_steps,
            "deferred_intents": session.deferred_intents,
            "ticket_created": session.ticket_created,
            "history": session.history,
            "created_at": getattr(session, "created_at", None),
            "in_memory": True,
        }
    data = load_session(session_id)
    if data:
        return {**data, "in_memory": False}
    raise HTTPException(404, f"Session {session_id} not found")


@app.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """Get just the message history for a session."""
    if session_id in _sessions:
        return {"session_id": session_id, "history": _sessions[session_id].history}
    data = load_session(session_id)
    if data:
        return {"session_id": session_id, "history": data.get("history", [])}
    raise HTTPException(404, f"Session {session_id} not found")


@app.post("/session/reset")
def reset(req: ResetRequest):
    reset_session(req.session_id)
    return {"status": "reset", "session_id": req.session_id}


@app.delete("/session/{session_id}")
def delete_session_endpoint(session_id: str):
    """Delete a session permanently from memory and disk."""
    _sessions.pop(session_id, None)
    deleted = delete_session(session_id)
    return {"status": "deleted" if deleted else "not_found", "session_id": session_id}


# ──────────────────────────────────────────────────────────────────
# FAQ Cache
# ──────────────────────────────────────────────────────────────────

@app.get("/cache/stats")
def cache_stats():
    """Cache statistics + trending FAQs."""
    return faq_cache.stats()


@app.get("/cache/trending")
def cache_trending():
    """Top frequently-asked questions, ranked by hit count."""
    stats = faq_cache.stats()
    return {"trending_faqs": stats["trending_faqs"]}


@app.delete("/cache")
def clear_cache():
    """Clear the entire FAQ cache."""
    faq_cache.clear()
    return {"status": "cleared"}


# ──────────────────────────────────────────────────────────────────
# Logs
# ──────────────────────────────────────────────────────────────────

def _tail_jsonl(path, n=100):
    """Read last n JSON lines from a file."""
    import json
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    last = lines[-n:]
    out = []
    for line in last:
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception as e:
            # Log parsing errors to console but don't break
            logger.debug(f"Failed to parse JSON line: {line.strip()[:100]} - {e}")
    return out


@app.get("/logs/pipeline")
def logs_pipeline(limit: int = 100, session_id: Optional[str] = None):
    """Pipeline events: message_received, kb_retrieved, llm_response, ticket_created, etc."""
    entries = _tail_jsonl(PIPELINE_LOG, n=limit * 5 if session_id else limit)
    if session_id:
        entries = [e for e in entries if e.get("session_id") == session_id]
        entries = entries[-limit:]
    return {"events": entries, "count": len(entries)}


@app.get("/logs/access")
def logs_access(limit: int = 100):
    """API access log."""
    entries = _tail_jsonl(ACCESS_LOG, n=limit)
    return {"requests": entries, "count": len(entries)}


@app.get("/logs/errors")
def logs_errors(limit: int = 100):
    """Recent errors."""
    entries = _tail_jsonl(ERROR_LOG, n=limit)
    return {"errors": entries, "count": len(entries)}