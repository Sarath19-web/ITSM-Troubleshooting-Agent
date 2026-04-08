import os
import re
import time
from datetime import datetime

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from app.config import (
    DB_PATH, EMBEDDING_MODEL, LLM_MODEL, RETRIEVAL_K, RERANK_TOP_N,
    LLM_NUM_PREDICT, LLM_TEMPERATURE, LLM_NUM_CTX,
    MAX_TROUBLESHOOT_TURNS, TICKET_CATEGORIES,
)
from app.services.tickets import ticket_service
from app.services.logger import get_logger, log_pipeline_event, Timer
from app.services.session_store import save_session, load_session, restore_into_session_object
from app.services.faq_cache import faq_cache

logger = get_logger("engine")

_db = None
_llm = None
_embeddings = None


def _get_db():
    global _db
    if _db is None:
        with Timer(logger, "init_chroma_db"):
            emb = _get_embeddings_model()
            _db = Chroma(persist_directory=DB_PATH, embedding_function=emb)
    return _db


def _get_embeddings_model():
    global _embeddings
    if _embeddings is None:
        with Timer(logger, "init_embeddings_model", model=EMBEDDING_MODEL):
            _embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    return _embeddings


def _get_llm():
    global _llm
    if _llm is None:
        print(f"Initializing LLM model {LLM_MODEL}...")
        with Timer(logger, "init_llm", model=LLM_MODEL):
            _llm = OllamaLLM(
                model=LLM_MODEL,
                num_predict=LLM_NUM_PREDICT,
                temperature=LLM_TEMPERATURE,
                num_ctx=LLM_NUM_CTX,
                stop=[
                    "\nUser:", "\nUSER:", "User said:", "The user just said",
                    "\n===", "=== ",
                    "\nAlex:", "\nAGENT:", "\nAssistant:",
                    "## YOUR RESPONSE", "## USER", "## CONVERSATION",
                ],
            )
    return _llm


def _embed_for_cache(text):
    """Embedding function for FAQ cache (injected at warmup)."""
    try:
        return _get_embeddings_model().embed_query(text)
    except Exception as e:
        logger.warning(f"Embed for cache failed: {e}")
        return None


PROBLEM_KEYWORDS = {
    "Network & VPN": ["vpn", "network", "wifi", "internet", "connect", "disconn", "offline"],
    "Email & Calendar": ["email", "outlook", "calendar", "mail", "inbox", "outbox", "meeting invite"],
    "Account & Access": ["password", "login", "locked", "account", "access", "mfa", "credential"],
    "Printer & Peripherals": ["printer", "print", "scanner", "monitor", "keyboard", "mouse", "usb"],
    "Performance": ["slow", "freeze", "hang", "crash", "blue screen", "bsod", "lag"],
    "Software & Apps": ["install", "software", "application", "license", "teams", "zoom", "slack"],
    "Hardware": ["laptop", "desktop", "screen", "battery", "charger", "broken", "damaged"],
    "Security": ["virus", "malware", "phishing", "suspicious", "hack", "breach"],
}

NEGATIVE_RESPONSES = ["no", "nope", "nah", "negative", "not yet", "haven't"]
POSITIVE_RESPONSES = ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "alright", "do it"]
ALREADY_TRIED = ["already tried", "tried that", "did that", "already did", "still not working",
                 "didn't work", "did not work", "doesn't work", "not working", "no luck",
                 "still broken", "still failing", "same issue", "not fixed", "not resolved"]


class ITSMSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.history = []
        self.current_category = None
        self.troubleshoot_turn = 0
        self.steps_completed = []
        self.failed_steps = []
        self.awaiting_clarification = False
        self.awaiting_ticket_confirmation = False
        self.draft_ticket = None
        self.deferred_intents = []
        self.resolved_intents = []
        self.clarifying_questions_asked = 0
        self.ticket_created = None
        self.user_name = None
        self.last_step_suggested = None
        self.created_at = datetime.utcnow().isoformat()

    def add_message(self, role, content, metadata=None):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def get_recent_context(self, n=8):
        return self.history[-n:] if self.history else []

    def reset(self):
        sid = self.session_id
        self.__init__(sid)


_sessions = {}


def get_session(session_id):
    """Get session from memory, or load from disk if not in memory."""
    if session_id in _sessions:
        return _sessions[session_id]

    data = load_session(session_id)
    if data:
        logger.info(f"Restoring session {session_id} from disk ({len(data.get('history',[]))} messages)")
        session = ITSMSession(session_id)
        restore_into_session_object(session, data)
        _sessions[session_id] = session
        return session

    logger.info(f"Creating new session {session_id}")
    _sessions[session_id] = ITSMSession(session_id)
    return _sessions[session_id]


def _detect_categories(question):
    q = question.lower()
    return [cat for cat, kws in PROBLEM_KEYWORDS.items() if any(k in q for k in kws)]


def _classify_intent(question, session=None):
    q = question.lower().strip()

    if session and (session.awaiting_clarification or session.awaiting_ticket_confirmation):
        if any(q == r or q.startswith(r + " ") for r in POSITIVE_RESPONSES):
            return "affirmative_response"
        if any(q == r or q.startswith(r + " ") for r in NEGATIVE_RESPONSES):
            return "negative_response"

    if any(s in q for s in ALREADY_TRIED):
        return "step_failed"

    ticket_signals = ["create ticket", "raise ticket", "log ticket", "open ticket",
                      "raise a ticket", "create a ticket", "submit ticket", "file a ticket"]
    if any(s in q for s in ticket_signals):
        return "create_ticket"

    resolved_signals = [
        "thank", "thx", "thnx", "appreciate", 
        "fixed", "resolved", "it works", "solved", 
        "you helped", "good now", "sorted", "perfect", "awesome"
    ]
    if any(s in q for s in resolved_signals) and not any(s in q for s in ["not", "didn't", "doesn't"]):
        return "issue_resolved"

    if re.search(r'inc\d{6}', q) or "ticket status" in q or "my ticket" in q or "check ticket" in q:
        return "ticket_status"

    has_problem = bool(_detect_categories(q))
    pure_greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    short_help = ["help", "help me", "i need help", "can you help"]

    if not has_problem and len(q) < 30:
        if q in pure_greetings or q in short_help:
            return "greeting"
        for g in pure_greetings:
            if q.startswith(g + " ") or q.startswith(g + ","):
                rest = q[len(g):].strip(" ,!.")
                if not rest or rest in short_help:
                    return "greeting"

    return "troubleshoot"


def _detect_priority(text):
    t = text.lower()
    if any(w in t for w in ["urgent", "critical", "emergency", "ceo", "vip", "production down"]):
        return "P1"
    if any(w in t for w in ["cannot work", "blocked", "deadline", "asap", "client meeting"]):
        return "P2"
    if any(w in t for w in ["minor", "low priority", "when possible"]):
        return "P4"
    return "P3"


def _retrieve_kb(question, category=None):
    db = _get_db()
    docs = []
    with Timer(logger, "kb_retrieval", category=category, k=RETRIEVAL_K):
        if category:
            try:
                docs = db.similarity_search(question, k=RETRIEVAL_K,
                    filter={"category": {"$eq": category}})
            except Exception as e:
                logger.warning(f"Filtered KB search failed: {e}")
        if not docs:
            docs = db.similarity_search(question, k=RETRIEVAL_K)

    seen, unique = set(), []
    for d in docs:
        h = hash(d.page_content[:150])
        if h not in seen:
            seen.add(h)
            unique.append(d)
    logger.debug(f"KB retrieval returned {len(unique)} unique chunks")
    return unique[:RERANK_TOP_N]


SYSTEM_PROMPT = """You are Alex, a friendly and patient IT Helpdesk Assistant at a Fortune 500 company.

## YOUR PERSONALITY
- Empathetic: Acknowledge frustration briefly
- Methodical: ONE specific step at a time
- Clear: Simple language, exact instructions

## CRITICAL RULES
1. NEVER give all troubleshooting steps at once. Give ONE step, then STOP.
2. Every step MUST be a specific action with exact instructions (e.g. "Click Start > Settings > System > Power & sleep" NOT "check your settings").
3. ALWAYS include exact paths, menu names, or commands. Users should be able to follow without guessing.
4. ALWAYS ask 1 clarifying question first if the issue is vague.
5. If user says "already tried that" or "didn't work" → MOVE TO NEXT STEP, never repeat.
6. DO NOT REPEAT previous questions or steps. Once the user replies, acknowledge and give a NEW step.
7. If KB doesn't have a clear answer → suggest creating a ticket.
8. After 4-5 unsuccessful steps → offer to create a ticket.
9. DO NOT add filler like "Let me know if this helps!" or "Would you like further assistance?". Just give the step and ask what happened.
10. ALWAYS end with a specific question like "Did that work?" or "What do you see now?".

## RESPONSE FORMAT
Use markdown: **bold** for important items, numbered lists for sub-steps.
Format: **Brief acknowledgment** → **Step N: Title** → **Numbered sub-steps** → **Short question**

Example:
> I understand — VPN disconnects can be disruptive. Let's fix this.
>
> **Step 1: Check your internet connection**
> 1. Open a browser
> 2. Go to **https://www.google.com**
> 3. Does the page load? ✓ or ✗

## WHEN TO CREATE A TICKET
Output EXACTLY this on its own lines (the system will parse it):

[CREATE_TICKET]
Summary: <one-line summary>
Category: <one of the categories>
Priority: <P1|P2|P3|P4>
Description: <2-3 sentences>
[/CREATE_TICKET]
"""


def _build_prompt(question, session, kb_chunks, intent_hint=""):
    context_parts = [f"[{d.metadata.get('category','?')}] {d.page_content[:600]}" for d in kb_chunks]
    kb_context = "\n---\n".join(context_parts) if context_parts else "(No KB articles found)"

    history_text = ""
    for h in session.get_recent_context(8):
        role = "User" if h["role"] == "user" else "Alex"
        history_text += f"{role}: {h['content'][:300]}\n"

    state_info = []
    if session.current_category:
        state_info.append(f"- Current issue category: {session.current_category}")
    state_info.append(f"- Troubleshooting turn: {session.troubleshoot_turn}/{MAX_TROUBLESHOOT_TURNS}")
    if session.steps_completed:
        state_info.append(f"- Steps already attempted: {', '.join(session.steps_completed[-3:])}")
    if session.failed_steps:
        state_info.append(f"- Steps that didn't work: {', '.join(session.failed_steps[-3:])}")
    if session.deferred_intents:
        state_info.append(f"- User also mentioned: {', '.join(session.deferred_intents)}")
    if session.troubleshoot_turn >= MAX_TROUBLESHOOT_TURNS - 1:
        state_info.append("- ⚠️ NEAR MAX TURNS — Strongly consider creating a ticket now.")
    if session.clarifying_questions_asked == 0 and session.troubleshoot_turn == 0:
        state_info.append("- This is the FIRST turn — ask a clarifying question first.")

    extra = ""
    if intent_hint == "step_failed":
        extra = "\n## IMPORTANT: User said the previous step DIDN'T WORK. Move to the NEXT step.\n"
    elif intent_hint == "negative_response":
        extra = "\n## IMPORTANT: User answered NO. Acknowledge and move forward differently.\n"
    elif intent_hint == "affirmative_response":
        extra = "\n## IMPORTANT: User answered YES. Proceed with next logical action.\n"
    elif intent_hint == "edit_ticket":
        extra = f"\n## IMPORTANT: User wants to edit the drafted ticket. Draft so far: {session.draft_ticket}. Output a rewritten [CREATE_TICKET] block reflecting their adjustments.\n"
    elif intent_hint == "create_ticket":
        extra = "\n## IMPORTANT: User specifically requested to create a ticket! STOP troubleshooting immediately and output a [CREATE_TICKET] block based on the context.\n"

    return f"""{SYSTEM_PROMPT}

=== SESSION STATE ===
{chr(10).join(state_info)}
{extra}
=== KNOWLEDGE BASE (use ONLY this information) ===
{kb_context}

=== CONVERSATION SO FAR ===
{history_text}
=== END ===

The user just said: {question}

Respond now as Alex with ONE next step. Do not continue the conversation on behalf of the user. Do not repeat these section headers. Write only Alex's reply:
"""


def _parse_ticket_block(response):
    match = re.search(r'\[CREATE_TICKET\](.*?)\[/CREATE_TICKET\]', response, re.DOTALL)
    if not match:
        return None
    block = match.group(1)
    data = {}
    for line in block.strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip().lower()] = val.strip()
    return data if "summary" in data else None


def _clean_response(response):
    # Remove ticket creation block (used internally, not shown to user)
    response = re.sub(r'\[CREATE_TICKET\].*?\[/CREATE_TICKET\]', '', response, flags=re.DOTALL)

    # ── Strip prompt leakage (model hallucinating prompt template) ──
    # Cut off at any point where the model started regenerating the prompt
    cutoff_markers = [
        "\nUser:", "\nUSER:", "User said:", "The user just said",
        "\n===", "=== ",
        "\nAlex:", "\nAGENT:", "\nAssistant:",
        "## YOUR RESPONSE", "## USER", "## CONVERSATION",
    ]
    for marker in cutoff_markers:
        idx = response.find(marker)
        if idx > 0:  # keep content before the marker
            response = response[:idx]

    # Remove any stray "User:" / "Alex:" at the start of lines
    response = re.sub(r'(?m)^\s*(User|USER|Alex|AGENT|Assistant)\s*:\s*.*$', '', response)

    # Collapse multiple blank lines
    response = re.sub(r'\n{3,}', '\n\n', response)

    return response.strip()


def _detect_step_attempted(text):
    m = re.search(r'\*\*Step \d+:?\s*([^*\n]+)\*\*', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'Step \d+:?\s*([^\n]+)', text)
    if m:
        return m.group(1).strip()[:60]
    return None


def _format_ticket_card(ticket):
    return (f"\n\n---\n\n### ✅ Ticket Created\n\n"
            f"**Ticket ID:** `{ticket['ticket_id']}`\n"
            f"**Priority:** {ticket['priority']} ({ticket['priority_label']})\n"
            f"**Category:** {ticket['category']}\n"
            f"**Assigned to:** {ticket['assigned_to']}\n"
            f"**Status:** {ticket['status']}\n\n"
            f"A specialist will follow up shortly. You can check status by asking about **{ticket['ticket_id']}**.")


def process_message(question, session_id, user_name=None):
    """Main entry point. Logged + cached + persisted."""
    overall_start = time.time()
    logger.info(f"━━━ NEW MESSAGE ━━━ session={session_id} q='{question[:60]}'")
    log_pipeline_event("message_received", session_id, {"question": question[:200], "user": user_name})

    session = get_session(session_id)
    if user_name:
        session.user_name = user_name

    session.add_message("user", question)
    intent = _classify_intent(question, session)
    logger.info(f"Classified intent: {intent}")

    if session.awaiting_ticket_confirmation and session.draft_ticket:
        if intent in ["affirmative_response", "issue_resolved"]:
            ticket = ticket_service.create_ticket(
                summary=session.draft_ticket.get("summary", "Support Ticket"),
                description=session.draft_ticket.get("description", ""),
                category=session.draft_ticket.get("category", session.current_category or "Other"),
                priority=session.draft_ticket.get("priority", _detect_priority(question)),
                session_id=session_id,
                user_name=session.user_name,
                troubleshooting_done=session.steps_completed,
                conversation_history=[{"role": h["role"], "content": h["content"]} for h in session.history],
            )
            session.ticket_created = ticket
            session.draft_ticket = None
            session.awaiting_ticket_confirmation = False
            msg = "I've successfully submitted your ticket!" + _format_ticket_card(ticket)
            session.add_message("agent", msg, {"intent": "ticket_created", "ticket_created": ticket["ticket_id"]})
            save_session(session)
            elapsed = (time.time() - overall_start) * 1000
            return _result(msg, session, elapsed, intent="ticket_created", ticket=ticket)
        elif intent == "negative_response":
            session.draft_ticket = None
            session.awaiting_ticket_confirmation = False
            msg = "Okay, I've cancelled the ticket draft. What would you like to do next?"
            session.add_message("agent", msg, {"intent": "ticket_cancelled"})
            save_session(session)
            elapsed = (time.time() - overall_start) * 1000
            return _result(msg, session, elapsed, intent="ticket_cancelled")
        else:
            intent = "edit_ticket"

    # ── Greeting
    if intent == "greeting":
        greeting = ("Hi there! I'm Alex, your IT Helpdesk Assistant 👋\n\n"
                    "I can help you troubleshoot technical issues — VPN, email, password, "
                    "printer, software, and more. Or I can create a support ticket for you.\n\n"
                    "**What's going on today?**")
        session.add_message("agent", greeting, {"intent": "greeting"})
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        log_pipeline_event("greeting_response", session_id, {"elapsed_ms": elapsed})
        return _result(greeting, session, elapsed, intent="greeting")

    # ── Ticket status
    if intent == "ticket_status":
        return _handle_ticket_status(question, session, overall_start)

    # ── Issue Resolved
    if intent == "issue_resolved":
        msg = "I'm glad to hear that's resolved!\n\n"
        if session.current_category and session.current_category not in session.resolved_intents:
            session.resolved_intents.append(session.current_category)

        session.steps_completed = []
        session.failed_steps = []
        session.troubleshoot_turn = 0
        session.awaiting_clarification = False
        session.last_step_suggested = None

        if session.deferred_intents:
            session.current_category = session.deferred_intents.pop(0)
            msg += "Here is the status of your reported issues:\n"
            for ri in session.resolved_intents:
                msg += f"- [x] {ri} (Resolved)\n"
            msg += f"- [ ] {session.current_category} (Pending)\n"
            for di in session.deferred_intents:
                msg += f"- [ ] {di} (Pending)\n"
            msg += f"\nWould you like to troubleshoot **{session.current_category}** now?"
        else:
            if session.resolved_intents:
                msg += "Here is the status of your reported issues:\n"
                for ri in session.resolved_intents:
                    msg += f"- [x] {ri} (Resolved)\n"
            session.current_category = None
            msg += "\nLooks like we've covered everything you mentioned. Is there anything else I can help you with today?"

        session.add_message("agent", msg, {"intent": "issue_resolved"})
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        log_pipeline_event("issue_resolved_response", session_id, {"elapsed_ms": elapsed})
        return _result(msg, session, elapsed, intent="issue_resolved")

    # ── Create Ticket (deterministic — bypass LLM entirely)
    if intent == "create_ticket":
        category = session.current_category or "Other"
        # Build summary from conversation context
        summary = f"{category} issue reported by user"
        # Build description from conversation history (filter out meta-commands)
        ticket_noise = ["create ticket", "raise ticket", "log ticket", "open ticket",
                        "create a ticket", "raise a ticket", "submit ticket", "file a ticket"]
        desc_parts = []
        seen_content = set()
        for h in session.history:
            if h["role"] == "user":
                text = h["content"].strip()
                text_lower = text.lower()
                # Skip ticket creation commands and duplicates
                if any(sig in text_lower for sig in ticket_noise):
                    continue
                if text_lower in seen_content:
                    continue
                seen_content.add(text_lower)
                desc_parts.append(f"- {text[:200]}")
        if session.steps_completed:
            desc_parts.append(f"\nTroubleshooting steps attempted: {', '.join(session.steps_completed)}")
        if session.failed_steps:
            desc_parts.append(f"Steps that did not resolve: {', '.join(session.failed_steps)}")
        description = "\n".join(desc_parts) if desc_parts else question

        draft = {
            "summary": summary,
            "description": description,
            "category": category,
            "priority": _detect_priority(" ".join(h["content"] for h in session.history if h["role"] == "user")),
        }
        session.draft_ticket = draft
        session.awaiting_ticket_confirmation = True

        msg = "I've drafted a support ticket based on our conversation. Please review the details below.\n\nSay **'yes'** to submit it, or tell me what you'd like to change."
        session.add_message("agent", msg, {"intent": "create_ticket", "draft_ticket": draft})
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        log_pipeline_event("ticket_drafted", session_id, {"draft": draft, "elapsed_ms": elapsed})
        return {
            **_result(msg, session, elapsed, intent="create_ticket"),
            "draft_ticket": draft,
        }

    # ── Step failed bookkeeping
    if intent == "step_failed" and session.last_step_suggested:
        session.failed_steps.append(session.last_step_suggested)
        logger.info(f"Step marked as failed: {session.last_step_suggested}")

    # ── Category detection + multi-intent
    categories = _detect_categories(question)
    if len(categories) > 1:
        session.deferred_intents = [c for c in categories[1:] if c not in session.deferred_intents]
        logger.info(f"Multi-intent detected. Deferred: {session.deferred_intents}")
    if categories and not session.current_category:
        session.current_category = categories[0]

    # ── KB unavailable fallback
    if not os.path.exists(DB_PATH):
        logger.error("KB database not found at " + DB_PATH)
        msg = ("I'm sorry — my knowledge base isn't available right now. "
               "Let me create a ticket so a specialist can help you directly.")
        session.add_message("agent", msg)
        session.awaiting_ticket_confirmation = True
        save_session(session)
        return _result(msg, session, (time.time() - overall_start) * 1000, intent="degraded")

    # ── ★★★ FAQ CACHE LOOKUP ★★★
    cached = None
    if intent == "troubleshoot" and session.troubleshoot_turn == 0:
        # Only check cache for fresh questions, not mid-conversation follow-ups
        cached = faq_cache.get(question, session.current_category)

    if cached:
        response = cached["response"]
        kb_sources = cached.get("kb_sources", [])
        session.troubleshoot_turn += 1
        session.add_message("agent", response, {
            "intent": intent,
            "category": session.current_category,
            "from_cache": True,
            "cache_type": cached.get("cache_type"),
            "cache_hits": cached.get("hit_count"),
        })
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        logger.info(f"⚡ CACHE HIT served in {elapsed:.1f}ms (vs ~5000ms LLM)")
        log_pipeline_event("cache_hit", session_id, {
            "question": question[:200],
            "cache_type": cached.get("cache_type"),
            "hit_count": cached.get("hit_count"),
            "elapsed_ms": elapsed,
        })
        return {
            "response": response,
            "session_id": session_id,
            "intent": intent,
            "category": session.current_category,
            "troubleshoot_turn": session.troubleshoot_turn,
            "max_turns": MAX_TROUBLESHOOT_TURNS,
            "deferred_intents": session.deferred_intents,
            "steps_completed": session.steps_completed,
            "failed_steps": session.failed_steps,
            "ticket": None,
            "response_time_ms": round(elapsed, 2),
            "kb_sources": kb_sources,
            "from_cache": True,
            "cache_type": cached.get("cache_type"),
        }

    # ── KB Retrieval
    kb_chunks = _retrieve_kb(question, session.current_category)
    log_pipeline_event("kb_retrieved", session_id, {"chunks": len(kb_chunks)})

    # ── LLM Call
    prompt = _build_prompt(question, session, kb_chunks, intent_hint=intent)
    raw = ""
    try:
        with Timer(logger, "llm_invoke", model=LLM_MODEL) as t:
            raw = _get_llm().invoke(prompt)
        log_pipeline_event("llm_response", session_id, {"elapsed_ms": t.elapsed_ms, "length": len(raw)})
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        log_pipeline_event("llm_error", session_id, {"error": str(e)})
        msg = ("I ran into a temporary issue. Please try again in a moment, "
               "or I can create a ticket for you now.")
        session.add_message("agent", msg, {"error": str(e)})
        save_session(session)
        return _result(msg, session, (time.time() - overall_start) * 1000, intent="error")

    ticket_data = _parse_ticket_block(raw)
    clean = _clean_response(raw)

    session.troubleshoot_turn += 1
    step_label = _detect_step_attempted(clean)
    if step_label:
        session.last_step_suggested = step_label
        if step_label not in session.steps_completed:
            session.steps_completed.append(step_label)

    if "?" in clean and session.troubleshoot_turn <= 2:
        session.awaiting_clarification = True
        session.clarifying_questions_asked += 1
    else:
        session.awaiting_clarification = False

    metadata = {
        "intent": intent,
        "category": session.current_category,
        "turn": session.troubleshoot_turn,
        "deferred_intents": session.deferred_intents,
        "kb_articles": [d.metadata.get("filename", d.metadata.get("source", "?")) for d in kb_chunks],
    }

    ticket = None
    if ticket_data:
        session.draft_ticket = ticket_data
        session.awaiting_ticket_confirmation = True
        clean = "I have drafted a support ticket for you. Does this look good to submit? (Say 'yes' to submit, or tell me what to change)"
        metadata["draft_ticket"] = ticket_data

    if (session.deferred_intents and session.troubleshoot_turn >= 1
            and not ticket and intent != "step_failed" and len(clean) > 100):
        deferred = session.deferred_intents[0]
        clean += (f"\n\n📌 *I haven't forgotten — you also mentioned a **{deferred}** issue "
                  f"which is in your pending checklist. "
                  f"Once we resolve this one, just let me know and we'll tackle that.*")

    session.add_message("agent", clean, metadata)

    kb_sources = [{
        "filename": d.metadata.get("filename", "?"),
        "category": d.metadata.get("category", "?"),
        "preview": d.page_content[:120],
    } for d in kb_chunks]

    # ── ★★★ FAQ CACHE STORE ★★★
    # Only cache if no ticket was created and response looks substantial
    if not ticket and len(clean) > 80 and session.troubleshoot_turn == 1:
        faq_cache.put(question, clean, session.current_category, kb_sources, intent)

    save_session(session)

    elapsed = (time.time() - overall_start) * 1000
    logger.info(f"━━━ MESSAGE COMPLETE ━━━ {elapsed:.1f}ms turn={session.troubleshoot_turn}")
    log_pipeline_event("message_complete", session_id, {"elapsed_ms": elapsed, "turn": session.troubleshoot_turn})

    return _result(clean, session, elapsed, intent=intent, ticket=ticket,
                  category=session.current_category, kb_chunks=kb_chunks)


def _handle_ticket_status(question, session, overall_start):
    match = re.search(r'INC\d{6}', question.upper())
    if match:
        ticket_id = match.group(0)
        ticket = ticket_service.get_ticket(ticket_id)
        if ticket:
            msg = (f"### 📋 Ticket Status: `{ticket['ticket_id']}`\n\n"
                   f"**Summary:** {ticket['summary']}\n"
                   f"**Status:** {ticket['status']}\n"
                   f"**Priority:** {ticket['priority']} ({ticket['priority_label']})\n"
                   f"**Category:** {ticket['category']}\n"
                   f"**Assigned to:** {ticket['assigned_to']}\n"
                   f"**Created:** {ticket['created_at'][:16]}")
            session.add_message("agent", msg, {"intent": "ticket_status", "ticket_id": ticket_id})
            save_session(session)
            return _result(msg, session, (time.time() - overall_start) * 1000,
                          intent="ticket_status", ticket=ticket)
        msg = f"I couldn't find ticket `{ticket_id}`. Could you double-check the ticket number?"
    else:
        tickets = ticket_service.get_all_tickets(status="Open")
        if tickets:
            msg = f"You have **{len(tickets)}** open ticket(s):\n\n"
            for t in tickets[:5]:
                msg += f"- **`{t['ticket_id']}`** — {t['summary'][:60]} *({t['status']})*\n"
            msg += "\nWhich ticket would you like me to check?"
        else:
            msg = "You don't have any open tickets at the moment. 🎉"
    session.add_message("agent", msg, {"intent": "ticket_status"})
    save_session(session)
    return _result(msg, session, (time.time() - overall_start) * 1000, intent="ticket_status")


def create_ticket_direct(session_id, summary, category=None, priority=None,
                         description=None, user_name=None):
    session = get_session(session_id)
    cat = category or session.current_category or "Other"
    pri = priority or _detect_priority(summary)
    desc = description or summary
    if session.steps_completed:
        desc += "\n\nSteps completed:\n" + "\n".join(f"- {s}" for s in session.steps_completed)
    if session.failed_steps:
        desc += "\n\nSteps that did NOT resolve:\n" + "\n".join(f"- {s}" for s in session.failed_steps)

    ticket = ticket_service.create_ticket(
        summary=summary, description=desc, category=cat, priority=pri,
        session_id=session_id, user_name=user_name or session.user_name,
        troubleshooting_done=session.steps_completed,
        conversation_history=[{"role": h["role"], "content": h["content"]} for h in session.history],
    )
    session.ticket_created = ticket
    save_session(session)
    logger.info(f"Direct ticket created: {ticket['ticket_id']}")
    return ticket


def _result(response, session, elapsed, intent=None, ticket=None, category=None, kb_chunks=None):
    return {
        "response": response,
        "session_id": session.session_id,
        "intent": intent,
        "category": category or session.current_category,
        "troubleshoot_turn": session.troubleshoot_turn,
        "max_turns": MAX_TROUBLESHOOT_TURNS,
        "deferred_intents": session.deferred_intents,
        "steps_completed": session.steps_completed,
        "failed_steps": session.failed_steps,
        "ticket": ticket,
        "draft_ticket": session.draft_ticket,
        "response_time_ms": round(elapsed, 2),
        "kb_sources": [{
            "filename": d.metadata.get("filename", "?"),
            "category": d.metadata.get("category", "?"),
            "preview": d.page_content[:120],
        } for d in (kb_chunks or [])],
        "from_cache": False,
    }


def reset_session(session_id):
    if session_id in _sessions:
        _sessions[session_id].reset()
        save_session(_sessions[session_id])
    logger.info(f"Session reset: {session_id}")


def warmup():
    """Initialize models and inject embedding function into FAQ cache."""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("ITSM Agent starting up...")
    try:
        _get_llm()
        _get_embeddings_model()
        faq_cache.set_embed_function(_embed_for_cache)
        logger.info(f"FAQ cache initialized with embedding function")
        stats = faq_cache.stats()
        logger.info(f"FAQ cache loaded: {stats['total_entries']} entries, {stats['total_hits']} total hits")
        logger.info("ITSM Agent ready to serve requests")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    except Exception as e:
        logger.error(f"Warmup failed: {e}", exc_info=True)