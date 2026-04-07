from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.engine import (
    process_message, create_ticket_direct, get_session,
    reset_session, warmup,
)
from app.services.tickets import ticket_service
from app.config import TICKET_CATEGORIES, TICKET_PRIORITIES

app = FastAPI(title="ITSM Troubleshooting Agent API", version="1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    warmup()


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


@app.get("/health")
def health():
    import os
    from app.config import DB_PATH
    return {
        "status": "healthy" if os.path.exists(DB_PATH) else "degraded",
        "agent": "ITSM Troubleshooting Agent v1.0",
        "kb_loaded": os.path.exists(DB_PATH),
    }


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
        "response_time_ms": result["response_time_ms"],
        "kb_sources": result["kb_sources"],
    }


@app.post("/tickets")
def create_ticket(req: TicketRequest):
    ticket = create_ticket_direct(
        session_id=req.session_id,
        summary=req.summary,
        category=req.category,
        priority=req.priority,
        description=req.description,
        user_name=req.user_name,
    )
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
            notes.append({"text": req.notes, "timestamp": __import__("datetime").datetime.now().isoformat()})
            updates["notes"] = notes
    result = ticket_service.update_ticket(ticket_id.upper(), updates)
    if not result:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    return {"status": "updated", "ticket": result}


@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    session = get_session(session_id)
    return {
        "session_id": session.session_id,
        "user_name": session.user_name,
        "message_count": len(session.history),
        "troubleshoot_turn": session.troubleshoot_turn,
        "max_turns": __import__("app.config", fromlist=["MAX_TROUBLESHOOT_TURNS"]).MAX_TROUBLESHOOT_TURNS,
        "current_category": session.current_category,
        "steps_completed": session.steps_completed,
        "failed_steps": session.failed_steps,
        "deferred_intents": session.deferred_intents,
        "clarifying_questions_asked": session.clarifying_questions_asked,
        "awaiting_clarification": session.awaiting_clarification,
        "ticket_created": session.ticket_created,
        "history": [{"role": h["role"], "content": h["content"],
                     "timestamp": h["timestamp"], "metadata": h.get("metadata", {})}
                    for h in session.history],
    }


@app.post("/session/reset")
def reset(req: ResetRequest):
    reset_session(req.session_id)
    return {"status": "reset", "session_id": req.session_id}


@app.get("/categories")
def categories():
    return {"categories": TICKET_CATEGORIES, "priorities": TICKET_PRIORITIES}