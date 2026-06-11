import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "database" / "bankops.db"


def get_customer_payment_status(customer_id: str):
    """
    Return the latest transaction status for a customer.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        c.customer_id,
        c.full_name,
        c.email,
        c.risk_level,
        t.transaction_id,
        t.amount,
        t.currency,
        t.status,
        t.failure_reason,
        t.created_at
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE c.customer_id = ?
    ORDER BY t.created_at DESC
    LIMIT 1
    """, (customer_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {"error": "Customer not found."}

    return dict(row)