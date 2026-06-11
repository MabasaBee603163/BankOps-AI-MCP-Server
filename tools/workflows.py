import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


DB_PATH = Path(__file__).resolve().parent.parent / "database" / "bankops.db"


VALID_WORKFLOW_STATUSES = {
    "started",
    "completed",
    "failed",
    "no_action_required",
}


def generate_workflow_id() -> str:
    """
    Generate a unique workflow ID.
    Example: WF-20260610-A8F32C
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = uuid4().hex[:6].upper()
    return f"WF-{date_part}-{random_part}"


def start_workflow_run(
    workflow_name: str,
    triggered_by_role: str,
    summary: str = ""
):
    """
    Create a new workflow run record with status 'started'.
    """
    workflow_id = generate_workflow_id()
    started_at = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO workflow_runs
    (workflow_id, workflow_name, status, started_at, completed_at, triggered_by_role, summary)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        workflow_id,
        workflow_name,
        "started",
        started_at,
        None,
        triggered_by_role,
        summary
    ))

    conn.commit()
    conn.close()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "status": "started",
        "started_at": started_at,
        "triggered_by_role": triggered_by_role,
        "summary": summary
    }


def update_workflow_run(
    workflow_id: str,
    status: str,
    summary: str = ""
):
    """
    Update a workflow run status.
    """
    status = status.strip().lower()

    if status not in VALID_WORKFLOW_STATUSES:
        return {
            "error": f"Invalid workflow status: {status}"
        }

    completed_at = None

    if status in {"completed", "failed", "no_action_required"}:
        completed_at = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE workflow_runs
    SET status = ?, completed_at = ?, summary = ?
    WHERE workflow_id = ?
    """, (
        status,
        completed_at,
        summary,
        workflow_id
    ))

    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()

    if rows_updated == 0:
        return {
            "error": "Workflow run not found."
        }

    return {
        "workflow_id": workflow_id,
        "status": status,
        "completed_at": completed_at,
        "summary": summary
    }


def complete_workflow_run(workflow_id: str, summary: str = ""):
    """
    Mark a workflow run as completed.
    """
    return update_workflow_run(
        workflow_id=workflow_id,
        status="completed",
        summary=summary
    )


def fail_workflow_run(workflow_id: str, summary: str = ""):
    """
    Mark a workflow run as failed.
    """
    return update_workflow_run(
        workflow_id=workflow_id,
        status="failed",
        summary=summary
    )


def mark_workflow_no_action_required(workflow_id: str, summary: str = ""):
    """
    Mark a workflow run as no_action_required.
    """
    return update_workflow_run(
        workflow_id=workflow_id,
        status="no_action_required",
        summary=summary
    )


def get_recent_workflow_runs(limit: int = 10):
    """
    Return recent workflow runs.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        workflow_id,
        workflow_name,
        status,
        started_at,
        completed_at,
        triggered_by_role,
        summary
    FROM workflow_runs
    ORDER BY started_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
    
def search_workflow_runs(
    workflow_name: str | None = None,
    status: str | None = None,
    triggered_by_role: str | None = None,
    limit: int = 10
):
    """
    Search workflow runs by workflow name, status, and triggering role.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        workflow_id,
        workflow_name,
        status,
        started_at,
        completed_at,
        triggered_by_role,
        summary
    FROM workflow_runs
    WHERE 1 = 1
    """

    params = []

    if workflow_name:
        query += " AND workflow_name = ?"
        params.append(workflow_name)

    if status:
        query += " AND status = ?"
        params.append(status)

    if triggered_by_role:
        query += " AND triggered_by_role = ?"
        params.append(triggered_by_role)

    query += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]