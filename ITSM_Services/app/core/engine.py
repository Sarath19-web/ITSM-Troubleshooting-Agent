import os
import re
import time
from datetime import datetime

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma

from app.config import (
    DB_PATH, EMBEDDING_MODEL, LLM_MODEL, RETRIEVAL_K, RERANK_TOP_N,
    LLM_NUM_PREDICT, LLM_TEMPERATURE, LLM_NUM_CTX,
    MAX_TROUBLESHOOT_TURNS, TICKET_CATEGORIES,
    LLM_PROVIDER, GROQ_API_KEY,
)
from app.services.tickets import ticket_service
from app.services.logger import get_logger, log_pipeline_event, Timer
from app.services.session_store import save_session, load_session, restore_into_session_object
from app.services.faq_cache import faq_cache
from app.core.guardrails import check_input, check_output

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
        print(f"Initializing LLM: provider={LLM_PROVIDER} model={LLM_MODEL}")
        with Timer(logger, "init_llm", model=LLM_MODEL, provider=LLM_PROVIDER):
            if LLM_PROVIDER == "groq":
                _llm = ChatGroq(
                    model=LLM_MODEL,
                    api_key=GROQ_API_KEY,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_NUM_PREDICT,
                    stop_sequences=[
                        "\nUser:", "\n===",
                        "## YOUR RESPONSE", "## CONVERSATION",
                    ],
                )
            else:
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


def _invoke_llm(prompt):
    """Invoke LLM and return plain text regardless of provider."""
    result = _get_llm().invoke(prompt)
    # ChatGroq returns AIMessage, OllamaLLM returns str
    if hasattr(result, 'content'):
        return result.content
    return str(result)


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
                 "still broken", "still failing", "same issue", "not fixed", "not resolved",
                 "nothing happened", "no change", "same problem"]

# Patterns indicating the user is reporting a step outcome (positive or negative)
_STEP_NEGATIVE_PATTERNS = [
    re.compile(r'(?:it|that|this|page|screen|the).*(?:not|isn\'t|doesn\'t|won\'t|can\'t|cannot).*(?:work|load|open|connect|start|show|display|appear|respond)', re.I),
    re.compile(r'(?:not|no|can\'t|cannot|couldn\'t)\s+(?:loading|working|connecting|opening|showing|displaying|appearing|responding)', re.I),
    re.compile(r'(?:still|keeps?)\s+(?:blank|black|frozen|stuck|loading|spinning|crashing|failing|disconnecting)', re.I),
    re.compile(r'(?:getting|shows?|see|seeing)\s+(?:an?\s+)?(?:error|blank|black screen|nothing|same)', re.I),
    re.compile(r'^(?:no|nope|nah|nothing|blank|black|error)\s*$', re.I),    re.compile(r'(?:no\s+)?(?:it\s+)?(?:doesn\'?t|does\s+not|didn\'?t|did\s+not)\s+(?:load|work|connect|open|help)', re.I),
    re.compile(r'(?:can\'?t|cannot|couldn\'?t)\s+(?:connect|load|open|access|reach|get)', re.I),]


class ITSMSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.history = []
        self.current_category = None
        self.original_issue = None          # ← stores the user's first problem description
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

    # Context-aware: if we're mid-troubleshooting and user describes a negative outcome
    if session and session.troubleshoot_turn > 0 and session.last_step_suggested:
        for pattern in _STEP_NEGATIVE_PATTERNS:
            if pattern.search(q):
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
    # Out-of-scope: no IT problem keywords detected and doesn't look like IT
    if not has_problem and not session:
        return "out_of_scope"
    if not has_problem and session and not session.current_category and session.troubleshoot_turn == 0:
        # Check if it's a general non-IT question
        it_terms = ["computer", "laptop", "desktop", "phone", "device", "app", "system",
                     "error", "issue", "problem", "broken", "not working", "help",
                     "fix", "troubleshoot", "ticket", "support", "reset", "update"]
        if not any(t in q for t in it_terms):
            return "out_of_scope"
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

## CRITICAL RULES — READ CAREFULLY
1. **READ THE CONVERSATION HISTORY BELOW.** Your response MUST continue logically from the last exchange.
2. NEVER give all troubleshooting steps at once. Give ONE step, then STOP.
3. Every step MUST be a specific action with exact instructions (e.g. "Click Start > Settings > System > Power & sleep" NOT "check your settings").
4. ALWAYS include exact paths, menu names, or commands. Users should be able to follow without guessing.
5. ALWAYS ask 1 clarifying question first if the issue is vague.
6. **NEVER REPEAT a step that already appears in the CONVERSATION HISTORY or in the STEPS ALREADY ATTEMPTED list.** If the user says "didn't work" or "already tried", give a COMPLETELY DIFFERENT next step.
7. **DO NOT REPEAT previous questions or steps.** If you already asked something or suggested something, move forward, not backward.
8. If KB doesn't have a clear answer → suggest creating a ticket.
9. After 4-5 unsuccessful steps → offer to create a ticket.
10. DO NOT add filler text. Just give the step and ask what happened.
11. ALWAYS end with a specific question like "Did that work?" or "What do you see now?".
12. The STEP NUMBER must continue from where we left off (see SESSION STATE below).

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

    # Build conversation history with clear turn markers
    history_text = ""
    for h in session.get_recent_context(10):
        role = "User" if h["role"] == "user" else "Alex"
        history_text += f"{role}: {h['content'][:400]}\n"

    state_info = []
    if session.current_category:
        state_info.append(f"- Current issue category: {session.current_category}")
    if session.original_issue:
        state_info.append(f"- Original problem reported: {session.original_issue[:200]}")
    state_info.append(f"- Troubleshooting turn: {session.troubleshoot_turn}/{MAX_TROUBLESHOOT_TURNS}")
    state_info.append(f"- Next step number to give: Step {session.troubleshoot_turn + 1}")
    if session.steps_completed:
        state_info.append(f"- ⚠ Steps ALREADY attempted (DO NOT REPEAT THESE): {', '.join(session.steps_completed)}")
    if session.failed_steps:
        state_info.append(f"- ⚠ Steps that FAILED (DO NOT REPEAT THESE): {', '.join(session.failed_steps)}")
    if session.deferred_intents:
        state_info.append(f"- User also mentioned: {', '.join(session.deferred_intents)}")
    if session.troubleshoot_turn >= MAX_TROUBLESHOOT_TURNS - 1:
        state_info.append("- ⚠️ NEAR MAX TURNS — Strongly consider creating a ticket now.")
    if session.clarifying_questions_asked == 0 and session.troubleshoot_turn == 0:
        state_info.append("- ⚠ This is the FIRST turn. You MUST ask 1-2 clarifying questions to understand the issue better BEFORE giving any troubleshooting steps.")
        state_info.append("- Examples: 'What exactly do you see on screen?', 'When did this start?', 'Is this a laptop or desktop?', 'Any error messages?'")
        state_info.append("- DO NOT give Step 1 yet. Just acknowledge and ask questions.")

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

=== SESSION STATE (read this carefully) ===
{chr(10).join(state_info)}
{extra}
=== KNOWLEDGE BASE (use ONLY this information for troubleshooting steps) ===
{kb_context}

=== CONVERSATION HISTORY (you MUST continue from where this left off) ===
{history_text}
=== END OF HISTORY ===

The user just said: "{question}"

IMPORTANT REMINDERS:
- Your next step number is Step {session.troubleshoot_turn + 1}.
- Do NOT repeat any step from the conversation above.
- Respond ONLY as Alex with ONE next step. Do not simulate user replies.

Alex:
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


def _is_repeated_step(step_label, session):
    """Check if a step label is semantically similar to any already attempted/failed step."""
    if not step_label:
        return False
    label_lower = step_label.lower()
    all_previous = session.steps_completed + session.failed_steps
    for prev in all_previous:
        prev_lower = prev.lower()
        # Exact or near-exact match
        if label_lower == prev_lower:
            return True
        # Significant word overlap (3+ shared words)
        words_new = set(re.findall(r'\w{3,}', label_lower))
        words_old = set(re.findall(r'\w{3,}', prev_lower))
        overlap = words_new & words_old
        if len(overlap) >= 2 and len(overlap) / max(len(words_new), 1) > 0.5:
            return True
    return False


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

    # ── Input Guardrails ──
    input_check = check_input(question)
    if not input_check.allowed:
        logger.warning(f"Input blocked: {input_check.flags}")
        log_pipeline_event("input_blocked", session_id, {"flags": input_check.flags, "reason": input_check.blocked_reason})
        session = get_session(session_id)
        session.add_message("user", question, {"guardrail_flags": input_check.flags})
        session.add_message("agent", input_check.blocked_reason, {"intent": "guardrail_blocked", "flags": input_check.flags})
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        return _result(input_check.blocked_reason, session, elapsed, intent="guardrail_blocked")
    # Use sanitized text (PII redacted) for downstream processing
    question = input_check.sanitized_text
    guardrail_flags = input_check.flags

    session = get_session(session_id)
    if user_name:
        session.user_name = user_name

    session.add_message("user", question, {"guardrail_flags": guardrail_flags} if guardrail_flags else None)
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

    # ── Out-of-scope (weather, general knowledge, etc.)
    if intent == "out_of_scope":
        msg = ("I appreciate you reaching out! However, I'm specifically designed to help with "
               "**IT support issues** — things like VPN, email, password resets, printer problems, "
               "software installations, and hardware issues.\n\n"
               "I'm not able to help with that particular question, but if you have any "
               "tech issues, I'm here for you! **What IT issue can I help you with?**")
        session.add_message("agent", msg, {"intent": "out_of_scope"})
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        log_pipeline_event("out_of_scope_response", session_id, {"question": question[:200], "elapsed_ms": elapsed})
        return _result(msg, session, elapsed, intent="out_of_scope")

    # ── Ticket status
    if intent == "ticket_status":
        return _handle_ticket_status(question, session, overall_start)

    # ── Issue Resolved / Thank you
    if intent == "issue_resolved":
        # If there's nothing active to resolve, treat as a goodbye/thank you
        if not session.current_category and not session.deferred_intents:
            msg = ("You're welcome! 😊 Happy I could help.\n\n"
                   "If you run into any other IT issues in the future, don't hesitate to reach out. "
                   "Have a great day!")
            session.add_message("agent", msg, {"intent": "goodbye"})
            save_session(session)
            elapsed = (time.time() - overall_start) * 1000
            log_pipeline_event("goodbye_response", session_id, {"elapsed_ms": elapsed})
            return _result(msg, session, elapsed, intent="goodbye")

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

    # ── Category detection + multi-intent + topic switching
    categories = _detect_categories(question)
    if len(categories) > 1:
        session.deferred_intents = [c for c in categories[1:] if c not in session.deferred_intents]
        logger.info(f"Multi-intent detected. Deferred: {session.deferred_intents}")

    # Detect topic switch: user raises a NEW category while one is active
    if categories and session.current_category and categories[0] != session.current_category:
        old_cat = session.current_category
        logger.info(f"Topic switch detected: {old_cat} → {categories[0]}")
        # Park the old issue as deferred if not resolved
        if old_cat not in session.resolved_intents and old_cat not in session.deferred_intents:
            session.deferred_intents.append(old_cat)
        # Reset troubleshooting state for the new topic
        session.current_category = categories[0]
        session.original_issue = question
        session.troubleshoot_turn = 0
        session.steps_completed = []
        session.failed_steps = []
        session.last_step_suggested = None
        session.awaiting_clarification = False
    elif categories and not session.current_category:
        session.current_category = categories[0]

    # Store original issue on first real troubleshoot turn
    if not session.original_issue and intent == "troubleshoot" and session.troubleshoot_turn == 0:
        session.original_issue = question

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

    # ── KB Retrieval (use original issue for follow-ups so we don't search "didn't work")
    kb_query = question
    if session.original_issue and session.troubleshoot_turn > 0:
        # Mid-troubleshooting: always use the original issue for KB unless user raised a new topic
        new_categories = _detect_categories(question)
        if not new_categories or (new_categories and new_categories[0] == session.current_category):
            kb_query = session.original_issue
            logger.info(f"Using original issue for KB retrieval: '{kb_query[:60]}'")
    kb_chunks = _retrieve_kb(kb_query, session.current_category)
    log_pipeline_event("kb_retrieved", session_id, {"chunks": len(kb_chunks)})

    # ── LLM Call (with repeat-step retry)
    prompt = _build_prompt(question, session, kb_chunks, intent_hint=intent)
    raw = ""
    try:
        with Timer(logger, "llm_invoke", model=LLM_MODEL) as t:
            raw = _invoke_llm(prompt)
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

    # ── Output Guardrails ──
    output_check = check_output(clean, session)
    if output_check.flags:
        logger.info(f"Output guardrail flags: {output_check.flags}")
        log_pipeline_event("output_guardrail", session_id, {"flags": output_check.flags})
    clean = output_check.sanitized_text

    # ── Repeated-step detection: retry once, then deterministic fallback ──
    step_label = _detect_step_attempted(clean)
    if step_label and _is_repeated_step(step_label, session):
        logger.warning(f"REPEATED STEP detected: '{step_label}' — retrying with explicit block list")
        retry_extra = (
            f"\n## CRITICAL: You just repeated a step the user already tried! The following steps have ALREADY BEEN DONE:\n"
            + "\n".join(f"- {s}" for s in (session.steps_completed + session.failed_steps))
            + "\n\nYou MUST give a COMPLETELY DIFFERENT troubleshooting step. "
            "Think of an alternative approach that is NOT listed above.\n"
        )
        retry_prompt = _build_prompt(question, session, kb_chunks, intent_hint=intent)
        # Inject the block list right before the final question
        retry_prompt = retry_prompt.replace(
            f'The user just said: "{question}"',
            f'{retry_extra}\nThe user just said: "{question}"'
        )
        try:
            with Timer(logger, "llm_retry", model=LLM_MODEL) as t2:
                raw2 = _invoke_llm(retry_prompt)
            clean2 = _clean_response(raw2)
            output_check2 = check_output(clean2, session)
            clean2 = output_check2.sanitized_text
            step_label2 = _detect_step_attempted(clean2)

            if step_label2 and _is_repeated_step(step_label2, session):
                # Still repeating — use deterministic fallback
                logger.warning(f"STILL REPEATED after retry: '{step_label2}' — using fallback")
                step_num = session.troubleshoot_turn + 1
                clean = (
                    f"I understand that didn't work. I've tried the standard troubleshooting steps "
                    f"for this issue and we're not making progress.\n\n"
                    f"**Step {step_num}: Let me escalate this**\n\n"
                    f"Since the previous steps haven't resolved your **{session.current_category or 'issue'}**, "
                    f"I'd recommend we create a support ticket so a specialist can look into this more deeply.\n\n"
                    f"Would you like me to **create a ticket** for you? Or is there something else you'd like to try?"
                )
                step_label = "Escalation recommended"
            else:
                clean = clean2
                step_label = step_label2
                ticket_data = _parse_ticket_block(raw2) or ticket_data
                logger.info(f"Retry succeeded with new step: '{step_label}'")
        except Exception as e:
            logger.error(f"LLM retry failed: {e}")
            # Keep the original response as-is

    session.troubleshoot_turn += 1
    if step_label:
        session.last_step_suggested = step_label
        if step_label not in session.steps_completed:
            session.steps_completed.append(step_label)

    if "?" in clean and session.troubleshoot_turn <= 2:
        session.awaiting_clarification = True
        session.clarifying_questions_asked += 1
    else:
        session.awaiting_clarification = False

    # ── Auto-escalation at max turns: agent takes charge and creates ticket
    if session.troubleshoot_turn >= MAX_TROUBLESHOOT_TURNS and not ticket_data:
        logger.info(f"Auto-escalation triggered at turn {session.troubleshoot_turn}/{MAX_TROUBLESHOOT_TURNS}")
        category = session.current_category or "Other"
        summary = f"{category} issue — unresolved after {session.troubleshoot_turn} troubleshooting steps"
        desc_parts = []
        if session.original_issue:
            desc_parts.append(f"Original issue: {session.original_issue[:200]}")
        if session.steps_completed:
            desc_parts.append(f"Steps attempted: {', '.join(session.steps_completed)}")
        if session.failed_steps:
            desc_parts.append(f"Steps that did not resolve: {', '.join(session.failed_steps)}")
        description = "\n".join(desc_parts) if desc_parts else question

        ticket = ticket_service.create_ticket(
            summary=summary,
            description=description,
            category=category,
            priority=_detect_priority(" ".join(h["content"] for h in session.history if h["role"] == "user")),
            session_id=session_id,
            user_name=session.user_name,
            troubleshooting_done=session.steps_completed,
            conversation_history=[{"role": h["role"], "content": h["content"]} for h in session.history],
        )
        session.ticket_created = ticket
        escalation_msg = (
            f"I've exhausted the troubleshooting steps available to me after **{session.troubleshoot_turn} attempts**, "
            f"and I want to make sure this gets resolved for you.\n\n"
            f"I've **automatically escalated** this to our specialist team by creating a support ticket."
            + _format_ticket_card(ticket)
            + "\n\nA specialist will review the full conversation history and follow up with you directly. "
            "Is there anything else I can help you with in the meantime?"
        )
        session.add_message("agent", escalation_msg, {
            "intent": "auto_escalation",
            "ticket_created": ticket["ticket_id"],
            "turn": session.troubleshoot_turn,
        })
        save_session(session)
        elapsed = (time.time() - overall_start) * 1000
        log_pipeline_event("auto_escalation", session_id, {
            "ticket_id": ticket["ticket_id"],
            "turns": session.troubleshoot_turn,
            "elapsed_ms": elapsed,
        })
        return _result(escalation_msg, session, elapsed, intent="auto_escalation", ticket=ticket,
                      category=session.current_category, kb_chunks=kb_chunks)

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