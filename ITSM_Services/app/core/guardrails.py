"""
Input and Output Guardrails for ITSM Agent.

Input guards:  sanitize user messages before processing.
Output guards: sanitize LLM responses before returning to user.
"""
import re
from app.services.logger import get_logger

logger = get_logger("guardrails")


# ─── PII Patterns ────────────────────────────────────────────────
_PII_PATTERNS = [
    # SSN
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "[SSN REDACTED]"),
    # Credit card (Visa, MC, Amex, Discover)
    (re.compile(r'\b(?:\d[ -]*?){13,19}\b'), None),  # handled by _is_credit_card
    # Email addresses in user input (redact to protect PII in logs/tickets)
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "[EMAIL REDACTED]"),
    # Phone numbers (US formats)
    (re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), "[PHONE REDACTED]"),
    # IP addresses (internal network info)
    (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), "[IP REDACTED]"),
]

# Luhn check for credit cards
def _luhn_check(num_str):
    digits = [int(d) for d in num_str if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse = digits[::-1]
    for i, d in enumerate(reverse):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

_CC_PATTERN = re.compile(r'\b[\d][\d\s-]{11,22}[\d]\b')


def _redact_pii(text):
    """Redact PII from text. Returns (cleaned_text, list_of_redactions)."""
    redactions = []

    # Credit cards (with Luhn validation)
    def _cc_replace(m):
        raw = m.group(0)
        digits_only = re.sub(r'\D', '', raw)
        if _luhn_check(digits_only):
            redactions.append("credit_card")
            return "[CARD REDACTED]"
        return raw
    text = _CC_PATTERN.sub(_cc_replace, text)

    # Other PII
    for pattern, replacement in _PII_PATTERNS:
        if replacement is None:
            continue
        matches = pattern.findall(text)
        if matches:
            redactions.append(replacement.strip("[]").lower().replace(" ", "_"))
            text = pattern.sub(replacement, text)

    return text, redactions


# ─── Prompt Injection Detection ──────────────────────────────────
_INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts)', re.I),
    re.compile(r'you\s+are\s+now\s+(?:a|an|the)\s+', re.I),
    re.compile(r'forget\s+(everything|all|your)\s+(you|instructions|rules)', re.I),
    re.compile(r'new\s+system\s+prompt', re.I),
    re.compile(r'override\s+(system|instructions|rules)', re.I),
    re.compile(r'act\s+as\s+(?:if\s+)?(?:you\s+are|a)\s+', re.I),
    re.compile(r'disregard\s+(your|all|the)\s+(instructions|rules|guidelines)', re.I),
    re.compile(r'pretend\s+(you\s+are|to\s+be)\s+', re.I),
    re.compile(r'(system|assistant)\s*:\s*', re.I),
    re.compile(r'<\s*/?\s*(?:system|instruction|prompt)', re.I),
    re.compile(r'\[\s*(?:SYSTEM|INST)', re.I),
    re.compile(r'do\s+not\s+follow\s+(?:your|the)\s+(?:rules|instructions)', re.I),
    re.compile(r'reveal\s+(?:your|the)\s+(?:system|hidden|secret)\s+prompt', re.I),
]


def _detect_injection(text):
    """Check for prompt injection attempts. Returns (is_injection, matched_pattern)."""
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)
    return False, None


# ─── Profanity / Abuse Detection ─────────────────────────────────
_ABUSE_PATTERNS = [
    re.compile(r'\b(?:fuck|shit|bitch|asshole|bastard|dick|cunt|damn\s*it)\b', re.I),
    re.compile(r'\b(?:kill|murder|bomb|attack|threat)\s+(?:you|the|this)\b', re.I),
]


def _detect_abuse(text):
    for pattern in _ABUSE_PATTERNS:
        if pattern.search(text):
            return True
    return False


# ─── Input Length / Spam Guard ────────────────────────────────────
MAX_INPUT_LENGTH = 2000
_REPEAT_PATTERN = re.compile(r'(.{3,}?)\1{4,}')  # same 3+ chars repeated 5+ times


def _detect_spam(text):
    if len(text) > MAX_INPUT_LENGTH:
        return True, "message_too_long"
    if _REPEAT_PATTERN.search(text):
        return True, "repetitive_spam"
    return False, None


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

class GuardrailResult:
    """Result of a guardrail check."""
    __slots__ = ("allowed", "sanitized_text", "blocked_reason", "flags")

    def __init__(self, allowed, sanitized_text, blocked_reason=None, flags=None):
        self.allowed = allowed
        self.sanitized_text = sanitized_text
        self.blocked_reason = blocked_reason
        self.flags = flags or []


def check_input(text):
    """
    Run all input guardrails on user message.
    Returns GuardrailResult with sanitized text or block reason.
    """
    flags = []

    # 1. Spam / length
    is_spam, spam_type = _detect_spam(text)
    if is_spam:
        logger.warning(f"INPUT BLOCKED — spam: {spam_type}")
        if spam_type == "message_too_long":
            return GuardrailResult(
                allowed=False,
                sanitized_text=text,
                blocked_reason="Your message is too long. Please keep it under 2000 characters and describe your issue concisely.",
                flags=["spam_blocked"],
            )
        return GuardrailResult(
            allowed=False,
            sanitized_text=text,
            blocked_reason="I couldn't process that message. Could you please describe your IT issue in a clear sentence?",
            flags=["spam_blocked"],
        )

    # 2. Prompt injection
    is_injection, matched = _detect_injection(text)
    if is_injection:
        logger.warning(f"INPUT BLOCKED — prompt injection attempt: '{matched}'")
        flags.append("injection_blocked")
        return GuardrailResult(
            allowed=False,
            sanitized_text=text,
            blocked_reason="I'm here to help with IT support issues. Could you describe the technical problem you're experiencing?",
            flags=flags,
        )

    # 3. Abuse detection — allow through but flag (de-escalate, don't block)
    if _detect_abuse(text):
        logger.warning(f"INPUT FLAGGED — abusive language detected")
        flags.append("abuse_detected")
        # Don't block — let the agent respond professionally

    # 4. PII redaction
    sanitized, redactions = _redact_pii(text)
    if redactions:
        logger.info(f"INPUT PII redacted: {redactions}")
        flags.extend(redactions)

    return GuardrailResult(allowed=True, sanitized_text=sanitized, flags=flags)


# ─── Output Guardrails ───────────────────────────────────────────

_SYSTEM_PROMPT_LEAKAGE = [
    re.compile(r'SYSTEM\s*PROMPT', re.I),
    re.compile(r'my\s+(?:system|hidden|secret)\s+(?:prompt|instructions)', re.I),
    re.compile(r'I\s+was\s+(?:told|instructed|programmed)\s+to', re.I),
    re.compile(r'my\s+(?:rules|guidelines|instructions)\s+(?:say|are|tell)', re.I),
    re.compile(r'SESSION\s+STATE', re.I),
    re.compile(r'KNOWLEDGE\s+BASE.*use\s+ONLY', re.I),
    re.compile(r'CONVERSATION\s+HISTORY.*MUST\s+continue', re.I),
    re.compile(r'===\s*(?:SESSION|KNOWLEDGE|CONVERSATION|END)', re.I),
]

_OUTPUT_PII_PATTERNS = [
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "[REDACTED]"),
    (re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), "[REDACTED]"),
]

_HALLUCINATED_TICKET = re.compile(r'INC\d{6}', re.I)


def check_output(text, session=None):
    """
    Run all output guardrails on agent response.
    Returns GuardrailResult with sanitized text.
    """
    flags = []
    sanitized = text

    # 1. System prompt leakage
    for pattern in _SYSTEM_PROMPT_LEAKAGE:
        if pattern.search(sanitized):
            logger.warning(f"OUTPUT — system prompt leakage detected, stripping")
            flags.append("prompt_leakage_stripped")
            # Cut at the leakage point
            match = pattern.search(sanitized)
            sanitized = sanitized[:match.start()].strip()
            if len(sanitized) < 20:
                sanitized = "Let me help you with your IT issue. Could you describe what's happening?"
            break

    # 2. PII in output
    for pattern, replacement in _OUTPUT_PII_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            flags.append("output_pii_redacted")
            logger.warning(f"OUTPUT — PII found in response, redacting")
            sanitized = pattern.sub(replacement, sanitized)

    # 3. Hallucinated ticket IDs (ticket IDs that don't exist in context)
    if session:
        real_ticket_ids = set()
        if session.ticket_created:
            real_ticket_ids.add(session.ticket_created.get("ticket_id", ""))
        for m in _HALLUCINATED_TICKET.finditer(sanitized):
            tid = m.group(0).upper()
            if tid not in real_ticket_ids:
                logger.warning(f"OUTPUT — hallucinated ticket ID {tid} removed")
                flags.append("hallucinated_ticket_removed")
                sanitized = sanitized.replace(m.group(0), "[ticket pending]")

    # 4. Empty or nonsensical response
    cleaned_check = re.sub(r'\s+', '', sanitized)
    if len(cleaned_check) < 5:
        logger.warning("OUTPUT — empty/nonsensical response, using fallback")
        flags.append("empty_response_fallback")
        sanitized = "I'm having trouble formulating a response. Could you rephrase your issue, or would you like me to create a support ticket?"

    return GuardrailResult(allowed=True, sanitized_text=sanitized, flags=flags)
