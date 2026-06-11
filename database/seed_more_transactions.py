import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "bankops.db"


def seed_more_failed_transactions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    customers = [
        ("CUST004", "Naledi Khumalo", "naledi@example.com", "medium"),
        ("CUST005", "Sipho Ndlovu", "sipho@example.com", "high"),
        ("CUST006", "Mpho Baloyi", "mpho@example.com", "low"),
        ("CUST007", "Karabo Sithole", "karabo@example.com", "medium"),
        ("CUST008", "Zanele Maseko", "zanele@example.com", "high"),
    ]

    transactions = [
        ("TXN006", "CUST004", 2450.00, "ZAR", "failed", "Payment gateway timeout", "2026-06-10"),
        ("TXN007", "CUST005", 7899.50, "ZAR", "failed", "Card declined", "2026-06-10"),
        ("TXN008", "CUST006", 320.00, "ZAR", "failed", "Insufficient funds", "2026-06-10"),
        ("TXN009", "CUST007", 12000.00, "ZAR", "failed", "Velocity check triggered", "2026-06-10"),
        ("TXN010", "CUST008", 5600.75, "ZAR", "failed", "Account temporarily blocked", "2026-06-10"),

        ("TXN011", "CUST004", 999.99, "ZAR", "successful", None, "2026-06-10"),
        ("TXN012", "CUST005", 1500.00, "ZAR", "pending", None, "2026-06-10"),
        ("TXN013", "CUST006", 430.20, "ZAR", "successful", None, "2026-06-09"),
        ("TXN014", "CUST007", 2200.00, "ZAR", "failed", "Beneficiary bank unavailable", "2026-06-09"),
        ("TXN015", "CUST008", 875.40, "ZAR", "failed", "Fraud rule match", "2026-06-09"),
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
    conn.close()

    print("Additional transactions seeded successfully.")


if __name__ == "__main__":
    seed_more_failed_transactions()