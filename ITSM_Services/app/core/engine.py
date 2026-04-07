import os
import re
import time
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import (
    DB_PATH, EMBEDDING_MODEL, LLM_MODEL, RETRIEVAL_K, RERANK_TOP_N,
    MAX_CONTEXT_CHARS, LLM_NUM_PREDICT, LLM_TEMPERATURE, LLM_NUM_CTX,
    MAX_TROUBLESHOOT_TURNS, TICKET_CATEGORIES,
)
from app.services.tickets import ticket_service

_db = None
_llm = None


def _get_db():
    global _db
    if _db is None:
        emb = OllamaEmbeddings(model=EMBEDDING_MODEL)
        _db = Chroma(persist_directory=DB_PATH, embedding_function=emb)
    return _db


def _get_llm():
    global _llm
    if _llm is None:
        _llm = OllamaLLM(
            model=LLM_MODEL,
            num_predict=LLM_NUM_PREDICT,
            temperature=LLM_TEMPERATURE,
            num_ctx=LLM_NUM_CTX,
        )
    return _llm


CLARIFYING_QUESTIONS = {
    "Network & VPN": [
        "What operating system are you using? (Windows / Mac / Linux)",
        "Are you working from the office, remote, or both?",
        "When did this start happening — today, or earlier?",
    ],
    "Email & Calendar": [
        "Are you using Outlook desktop, Outlook web, or the mobile app?",
        "Do you see any specific error message?",
        "Is this affecting just you, or others on your team too?",
    ],
    "Account & Access": [
        "Is your account fully locked out, or are you just unable to reset your password?",
        "Did you recently change your password?",
        "Do you have access to your registered phone or backup email for verification?",
    ],
    "Printer & Peripherals": [
        "Which printer are you trying to use? (model or location)",
        "Is the printer showing any error on its display panel?",
        "Are other people able to print to it, or is it affecting everyone?",
    ],
    "Performance": [
        "Is this happening with one specific application, or across the whole system?",
        "Does it happen right after startup, or after the laptop has been running for a while?",
        "How old is your laptop, roughly?",
    ],
    "Software & Apps": [
        "Which application are you having trouble with?",
        "Is it failing to install, crashing, or showing an error?",
        "When did this start — after a recent update, or always?",
    ],
}

PROBLEM_KEYWORDS = {
    "Network & VPN": ["vpn", "network", "wifi", "internet", "connect", "disconn", "offline"],
    "Email & Calendar": ["email", "outlook", "calendar", "mail", "inbox", "outbox", "meeting invite"],
    "Account & Access": ["password", "login", "locked", "account", "access", "mfa", "credential"],
    "Printer & Peripherals": ["printer", "print", "scanner", "monitor", "keyboard", "mouse", "usb", "display"],
    "Performance": ["slow", "freeze", "hang", "crash", "blue screen", "bsod", "lag", "performance"],
    "Software & Apps": ["install", "software", "application", "license", "teams", "zoom", "slack", "onedrive"],
    "Hardware": ["laptop", "desktop", "screen", "battery", "charger", "broken", "damaged"],
    "Security": ["virus", "malware", "phishing", "suspicious", "hack", "breach"],
}

NEGATIVE_RESPONSES = ["no", "nope", "nah", "negative", "not yet", "not done", "haven't"]
POSITIVE_RESPONSES = ["yes", "yeah", "yep", "yup", "yes please", "sure", "ok", "okay", "alright", "do it"]
ALREADY_TRIED = ["already tried", "tried that", "did that", "already did", "still not working",
                 "didn't work", "did not work", "doesn't work", "not working", "no luck",
                 "still broken", "still failing", "same issue"]


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
        self.deferred_intents = []
        self.clarifying_questions_asked = 0
        self.ticket_created = None
        self.user_name = None
        self.last_step_suggested = None

    def add_message(self, role, content, metadata=None):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "metadata": metadata or {},
        })

    def get_recent_context(self, n=8):
        return self.history[-n:] if self.history else []

    def reset(self):
        self.__init__(self.session_id)


_sessions = {}


def get_session(session_id):
    if session_id not in _sessions:
        _sessions[session_id] = ITSMSession(session_id)
    return _sessions[session_id]


def _detect_categories(question):
    q = question.lower()
    found = []
    for cat, keywords in PROBLEM_KEYWORDS.items():
        if any(k in q for k in keywords):
            found.append(cat)
    return found


def _classify_intent(question, session=None):
    q = question.lower().strip()

    if session and (session.awaiting_clarification or session.awaiting_ticket_confirmation):
        if any(q == r or q.startswith(r + " ") or q.startswith(r + ",") for r in POSITIVE_RESPONSES):
            return "affirmative_response"
        if any(q == r or q.startswith(r + " ") or q.startswith(r + ",") for r in NEGATIVE_RESPONSES):
            return "negative_response"

    if any(s in q for s in ALREADY_TRIED):
        return "step_failed"

    ticket_signals = ["create ticket", "raise ticket", "log ticket", "open ticket",
                      "raise a ticket", "create a ticket", "raise an incident",
                      "submit ticket", "file a ticket"]
    if any(s in q for s in ticket_signals):
        return "create_ticket"

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
    if any(w in t for w in ["urgent", "critical", "emergency", "ceo", "vip",
                             "production down", "entire team", "all users", "executive"]):
        return "P1"
    if any(w in t for w in ["cannot work", "blocked", "deadline", "important meeting",
                             "asap", "multiple users", "client meeting"]):
        return "P2"
    if any(w in t for w in ["minor", "low priority", "when possible", "not urgent"]):
        return "P4"
    return "P3"


def _retrieve_kb(question, category=None):
    db = _get_db()
    docs = []
    if category:
        try:
            docs = db.similarity_search(question, k=RETRIEVAL_K,
                filter={"category": {"$eq": category}})
        except Exception:
            pass
    if not docs:
        docs = db.similarity_search(question, k=RETRIEVAL_K)
    seen = set()
    unique = []
    for d in docs:
        h = hash(d.page_content[:150])
        if h not in seen:
            seen.add(h)
            unique.append(d)
    return unique[:RERANK_TOP_N]


SYSTEM_PROMPT = """You are Alex, a friendly and patient IT Helpdesk Assistant at a Fortune 500 company. Your job is to help employees resolve IT issues through clear, step-by-step troubleshooting.

## YOUR PERSONALITY
- **Empathetic**: Acknowledge frustration ("I understand this is frustrating, let's fix it together")
- **Patient**: Never rush, never overwhelm
- **Methodical**: ONE step at a time, never dump all instructions at once
- **Clear**: Use simple language, avoid jargon
- **Confident but humble**: When you don't know, admit it and offer to escalate

## CRITICAL RULES (NEVER BREAK THESE)
1. **NEVER give all troubleshooting steps at once.** Give ONE step, wait for the user to try it, then give the next.
2. **ALWAYS use markdown formatting**: **bold** for important items, numbered lists for steps, line breaks between sections.
3. **ALWAYS ask 1 clarifying question first** if the issue is vague (e.g., "My computer is slow" → ask what application).
4. If the user says "already tried that" or "didn't work" → MOVE TO THE NEXT STEP, never repeat.
5. If KB doesn't have a clear answer → suggest creating a ticket.
6. After 4-5 unsuccessful steps → offer to create a ticket.

## RESPONSE FORMAT
**Acknowledge** → **Step** → **Wait for response**

Example structure:
> I understand — VPN disconnects can be really disruptive. Let's get this sorted.
>
> **Step 1: Check your internet connection**
> 1. Open a browser
> 2. Visit https://www.google.com
> 3. Let me know if the page loads ✓ or fails ✗

## WHEN TO CREATE A TICKET
Suggest a ticket when:
- 4+ troubleshooting steps tried without success
- KB doesn't cover the specific issue
- Issue requires admin/specialist intervention
- User explicitly asks for a ticket

When ready to create, output EXACTLY this on its own lines (the system will parse it):

[CREATE_TICKET]
Summary: <one-line summary of the issue>
Category: <one of: Network & VPN, Email & Calendar, Account & Access, Printer & Peripherals, Performance, Software & Apps, Hardware, Security>
Priority: <P1|P2|P3|P4>
Description: <2-3 sentences: what the issue is, what was tried, current state>
[/CREATE_TICKET]

## EXAMPLES OF GOOD vs BAD RESPONSES

❌ BAD (dumps everything):
"Try these: 1) Restart VPN 2) Clear cache 3) Reinstall 4) Check firewall 5) Update client"

✅ GOOD (one step, friendly):
"Got it — VPN issues can be a few different things. Let's start simple.
**Step 1: Restart the VPN client**
1. Right-click the VPN icon in your system tray
2. Click 'Quit' (not just close the window)
3. Wait 10 seconds, then relaunch from the Start menu
Let me know how that goes!"

❌ BAD (no clarifying question):
User: "My computer is slow"
Agent: "Try clearing temp files..."

✅ GOOD (asks first):
User: "My computer is slow"
Agent: "I can definitely help with that. To narrow it down — is this happening with one specific app, or is everything slow? And does it start slow right after boot, or only after running for a while?"
"""


def _build_prompt(question, session, kb_chunks, intent_hint=""):
    context_parts = []
    for d in kb_chunks:
        context_parts.append(f"[{d.metadata.get('category','?')}] {d.page_content[:600]}")
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
        state_info.append("- This is the FIRST turn — ask a clarifying question before suggesting steps.")

    state_text = "\n".join(state_info) if state_info else "(No session state yet)"

    extra_hint = ""
    if intent_hint == "step_failed":
        extra_hint = "\n## IMPORTANT: User said the previous step DIDN'T WORK. Move to the NEXT troubleshooting step (do not repeat the same one).\n"
    elif intent_hint == "negative_response":
        extra_hint = "\n## IMPORTANT: User answered NO to your previous question/suggestion. Acknowledge and move forward differently.\n"
    elif intent_hint == "affirmative_response":
        extra_hint = "\n## IMPORTANT: User answered YES. Proceed with the next logical action.\n"

    prompt = f"""{SYSTEM_PROMPT}

## SESSION STATE
{state_text}
{extra_hint}
## KB ARTICLES (use ONLY this information)
{kb_context}

## CONVERSATION HISTORY
{history_text}

## USER'S NEW MESSAGE
{question}

## YOUR RESPONSE (as Alex):"""
    return prompt


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
    response = re.sub(r'\[CREATE_TICKET\].*?\[/CREATE_TICKET\]', '', response, flags=re.DOTALL)
    return response.strip()


def _detect_step_attempted(text):
    """Extract a short label of what step the agent suggested."""
    m = re.search(r'\*\*Step \d+:?\s*([^*\n]+)\*\*', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'Step \d+:?\s*([^\n]+)', text)
    if m:
        return m.group(1).strip()[:60]
    return None


def process_message(question, session_id, user_name=None):
    session = get_session(session_id)
    if user_name:
        session.user_name = user_name

    session.add_message("user", question)
    start = time.time()

    intent = _classify_intent(question, session)

    if intent == "greeting":
        greeting = ("Hi there! I'm Alex, your IT Helpdesk Assistant 👋\n\n"
                    "I can help you troubleshoot technical issues — VPN, email, password, "
                    "printer, software, and more. Or if you already know what you need, "
                    "I can create a support ticket for you.\n\n"
                    "**What's going on today?**")
        session.add_message("agent", greeting, {"intent": "greeting"})
        return _result(greeting, session, time.time() - start, intent="greeting")

    if intent == "ticket_status":
        return _handle_ticket_status(question, session, start)

    if intent == "step_failed" and session.last_step_suggested:
        session.failed_steps.append(session.last_step_suggested)

    categories = _detect_categories(question)
    if len(categories) > 1:
        session.deferred_intents = [c for c in categories[1:]
                                     if c not in session.deferred_intents]
    if categories and not session.current_category:
        session.current_category = categories[0]
    elif categories and session.current_category not in categories and intent == "troubleshoot":
        if session.current_category:
            if categories[0] not in session.deferred_intents and categories[0] != session.current_category:
                session.deferred_intents.append(categories[0])

    if not os.path.exists(DB_PATH):
        msg = ("I'm sorry — my knowledge base isn't available right now. "
               "Let me create a ticket so a specialist can help you directly.")
        session.add_message("agent", msg)
        session.awaiting_ticket_confirmation = True
        return _result(msg, session, time.time() - start, intent="degraded")

    kb_chunks = _retrieve_kb(question, session.current_category)
    prompt = _build_prompt(question, session, kb_chunks, intent_hint=intent)
    raw = _get_llm().invoke(prompt)

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
        "kb_articles": [d.metadata.get("filename", d.metadata.get("source", "?"))
                        for d in kb_chunks],
        "chunks_used": [{
            "doc_type": d.metadata.get("doc_type", "?"),
            "category": d.metadata.get("category", "?"),
            "preview": d.page_content[:150],
        } for d in kb_chunks],
    }

    ticket = None
    if ticket_data:
        ticket = ticket_service.create_ticket(
            summary=ticket_data.get("summary", question[:100]),
            description=ticket_data.get("description", question),
            category=ticket_data.get("category", session.current_category or "Other"),
            priority=ticket_data.get("priority", _detect_priority(question)),
            session_id=session_id,
            user_name=session.user_name,
            troubleshooting_done=session.steps_completed,
            conversation_history=[{"role": h["role"], "content": h["content"]}
                                  for h in session.history],
        )
        session.ticket_created = ticket
        metadata["ticket_created"] = ticket["ticket_id"]
        clean += _format_ticket_card(ticket)

    if (session.deferred_intents and
        session.troubleshoot_turn >= 1 and
        not ticket and
        intent != "step_failed" and
        len(clean) > 100):
        deferred = session.deferred_intents[0]
        clean += (f"\n\n📌 *I haven't forgotten — you also mentioned a **{deferred}** issue. "
                  f"Once we resolve this one, just say 'next issue' and we'll tackle that.*")

    session.add_message("agent", clean, metadata)
    elapsed = time.time() - start

    return _result(clean, session, elapsed, intent=intent, ticket=ticket,
                  category=session.current_category, kb_chunks=kb_chunks)


def _format_ticket_card(ticket):
    return (f"\n\n---\n\n"
            f"### ✅ Ticket Created\n\n"
            f"**Ticket ID:** `{ticket['ticket_id']}`\n"
            f"**Priority:** {ticket['priority']} ({ticket['priority_label']})\n"
            f"**Category:** {ticket['category']}\n"
            f"**Assigned to:** {ticket['assigned_to']}\n"
            f"**Status:** {ticket['status']}\n\n"
            f"A specialist will follow up with you shortly. "
            f"You can check the status anytime by asking me about **{ticket['ticket_id']}**.")


def _handle_ticket_status(question, session, start):
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
                   f"**Created:** {ticket['created_at'][:16]}\n"
                   f"**Last updated:** {ticket['updated_at'][:16]}")
            if ticket.get("notes"):
                msg += "\n\n**Recent notes:**"
                for note in ticket["notes"][-3:]:
                    msg += f"\n- {note.get('text', '')}"
            session.add_message("agent", msg, {"intent": "ticket_status", "ticket_id": ticket_id})
            return _result(msg, session, time.time() - start,
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
    return _result(msg, session, time.time() - start, intent="ticket_status")


def create_ticket_direct(session_id, summary, category=None, priority=None,
                         description=None, user_name=None):
    session = get_session(session_id)
    cat = category or session.current_category or "Other"
    pri = priority or _detect_priority(summary)
    desc = description or summary
    if session.steps_completed:
        desc += "\n\nTroubleshooting steps completed:\n" + "\n".join(f"- {s}" for s in session.steps_completed)
    if session.failed_steps:
        desc += "\n\nSteps that did NOT resolve:\n" + "\n".join(f"- {s}" for s in session.failed_steps)

    ticket = ticket_service.create_ticket(
        summary=summary, description=desc, category=cat, priority=pri,
        session_id=session_id, user_name=user_name or session.user_name,
        troubleshooting_done=session.steps_completed,
        conversation_history=[{"role": h["role"], "content": h["content"]} for h in session.history],
    )
    session.ticket_created = ticket
    return ticket


def _result(response, session, elapsed, intent=None, ticket=None,
           category=None, kb_chunks=None):
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
        "response_time_ms": round(elapsed * 1000, 2),
        "kb_sources": [{
            "filename": d.metadata.get("filename", "?"),
            "category": d.metadata.get("category", "?"),
            "preview": d.page_content[:120],
        } for d in (kb_chunks or [])],
    }


def reset_session(session_id):
    if session_id in _sessions:
        _sessions[session_id].reset()


def warmup():
    try:
        _get_llm()
    except Exception:
        pass