import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


DB_PATH = Path(__file__).resolve().parent.parent / "database" / "bankops.db"


def create_support_ticket(title: str, priority: str, description: str):
    """
    Create a support ticket.

    The AI cannot invent random ticket priorities.
    Only approved values are accepted.
    """
    allowed_priorities = {"low", "medium", "high", "critical"}

    priority = priority.lower().strip()

    if priority not in allowed_priorities:
        return {
            "error": f"Invalid priority. Allowed values: {sorted(allowed_priorities)}"
        }

    ticket_id = f"TICKET-{uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO support_tickets
    (ticket_id, title, priority, description, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (ticket_id, title, priority, description, "open", created_at))

    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "title": title,
        "priority": priority,
        "status": "open",
        "created_at": created_at
    }
