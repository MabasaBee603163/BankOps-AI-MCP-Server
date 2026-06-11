import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "database" / "bankops.db"


def get_failed_transactions(date: str):
    """
    Return all failed transactions for a specific date.

    Security note:
    This function uses a predefined SQL query.
    The LLM never receives permission to send raw SQL.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        transaction_id,
        customer_id,
        amount,
        currency,
        failure_reason,
        created_at
    FROM transactions
    WHERE status = ? AND created_at = ?
    """, ("failed", date))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_transaction_summary(date: str):
    """
    Return grouped transaction totals for a specific date.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        status,
        COUNT(*) AS total_count,
        COALESCE(SUM(amount), 0) AS total_amount
    FROM transactions
    WHERE created_at = ?
    GROUP BY status
    """, (date,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]