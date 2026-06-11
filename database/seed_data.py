import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bankops.db"


def create_connection():
    return sqlite3.connect(DB_PATH)


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        risk_level TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL,
        failure_reason TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        ticket_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        priority TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflow_runs (
        workflow_id TEXT PRIMARY KEY,
        workflow_name TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        triggered_by_role TEXT NOT NULL,
        summary TEXT
    )
    """)

    conn.commit()


def seed_data(conn):
    cursor = conn.cursor()

    customers = [
        ("CUST001", "Amina Dlamini", "amina@example.com", "low"),
        ("CUST002", "Thabo Mokoena", "thabo@example.com", "medium"),
        ("CUST003", "Lerato Nkosi", "lerato@example.com", "high"),
    ]

    transactions = [
        ("TXN001", "CUST001", 1200.50, "ZAR", "successful", None, "2026-06-10"),
        ("TXN002", "CUST002", 899.99, "ZAR", "failed", "Insufficient funds", "2026-06-10"),
        ("TXN003", "CUST003", 4500.00, "ZAR", "failed", "Card blocked", "2026-06-10"),
        ("TXN004", "CUST001", 300.00, "ZAR", "pending", None, "2026-06-10"),
        ("TXN005", "CUST002", 150.75, "ZAR", "successful", None, "2026-06-09"),
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO customers 
    (customer_id, full_name, email, risk_level)
    VALUES (?, ?, ?, ?)
    """, customers)

    cursor.executemany("""
    INSERT OR REPLACE INTO transactions
    (transaction_id, customer_id, amount, currency, status, failure_reason, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    conn.commit()


def main():
    conn = create_connection()
    create_tables(conn)
    seed_data(conn)
    conn.close()
    print(f"Database created successfully at: {DB_PATH}")


if __name__ == "__main__":
    main()