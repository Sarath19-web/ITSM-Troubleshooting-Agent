import json
import os
from datetime import datetime
from app.config import TICKETS_FILE, TICKET_PRIORITIES, TICKET_CATEGORIES


class TicketService:

    def __init__(self):
        self.tickets = self._load()
        self._counter = max((t.get("number", 0) for t in self.tickets), default=1000)

    def _load(self):
        if os.path.exists(TICKETS_FILE):
            try:
                with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self):
        os.makedirs(os.path.dirname(TICKETS_FILE), exist_ok=True)
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tickets, f, indent=2, ensure_ascii=False)

    def create_ticket(self, summary, description, category="Other", priority="P3",
                      session_id=None, user_name=None, troubleshooting_done=None,
                      conversation_history=None):
        self._counter += 1
        ticket = {
            "ticket_id": f"INC{self._counter:06d}",
            "number": self._counter,
            "status": "Open",
            "priority": priority,
            "priority_label": TICKET_PRIORITIES.get(priority, "Medium"),
            "category": category,
            "summary": summary,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "assigned_to": self._auto_assign(category, priority),
            "user_name": user_name or "Unknown User",
            "session_id": session_id,
            "troubleshooting_steps_completed": troubleshooting_done or [],
            "conversation_summary": self._summarize_conversation(conversation_history),
            "notes": [],
        }
        self.tickets.append(ticket)
        self._save()
        return ticket

    def get_ticket(self, ticket_id):
        for t in self.tickets:
            if t["ticket_id"] == ticket_id:
                return t
        return None

    def update_ticket(self, ticket_id, updates):
        for t in self.tickets:
            if t["ticket_id"] == ticket_id:
                t.update(updates)
                t["updated_at"] = datetime.now().isoformat()
                self._save()
                return t
        return None

    def get_all_tickets(self, status=None, priority=None, category=None):
        filtered = self.tickets
        if status:
            filtered = [t for t in filtered if t["status"].lower() == status.lower()]
        if priority:
            filtered = [t for t in filtered if t["priority"] == priority]
        if category:
            filtered = [t for t in filtered if t["category"] == category]
        return sorted(filtered, key=lambda t: t["created_at"], reverse=True)

    def get_stats(self):
        total = len(self.tickets)
        if total == 0:
            return {"total": 0, "open": 0, "in_progress": 0, "resolved": 0, "closed": 0}
        by_status = {}
        by_priority = {}
        by_category = {}
        for t in self.tickets:
            s = t.get("status", "Open")
            by_status[s] = by_status.get(s, 0) + 1
            p = t.get("priority", "P3")
            by_priority[p] = by_priority.get(p, 0) + 1
            c = t.get("category", "Other")
            by_category[c] = by_category.get(c, 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "open": by_status.get("Open", 0),
            "in_progress": by_status.get("In Progress", 0),
            "resolved": by_status.get("Resolved", 0),
        }

    def _auto_assign(self, category, priority):
        assign_map = {
            "Network & VPN": "Network Team",
            "Email & Calendar": "Messaging Team",
            "Hardware": "Desktop Support",
            "Software & Apps": "App Support",
            "Account & Access": "Identity Team",
            "Printer & Peripherals": "Desktop Support",
            "Performance": "Desktop Support",
            "Security": "Security Operations",
        }
        team = assign_map.get(category, "General IT Support")
        if priority in ("P1", "P2"):
            team += " (Escalated)"
        return team

    def _summarize_conversation(self, history):
        if not history:
            return ""
        parts = []
        for h in history[-8:]:
            role = h.get("role", "user")
            content = h.get("content", "")[:300]
            parts.append(f"[{role.upper()}] {content}")
        return "\n".join(parts)


ticket_service = TicketService()
