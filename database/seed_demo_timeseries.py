import json
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DB_PATH = BASE_DIR / "bankops.db"
AUDIT_LOG_PATH = ROOT_DIR / "logs" / "audit_log.jsonl"

CUSTOMER_NAMES = [
    "Amina Dlamini",
    "Thabo Mokoena",
    "Lerato Nkosi",
    "Naledi Khumalo",
    "Sipho Ndlovu",
    "Mpho Baloyi",
    "Karabo Sithole",
    "Zanele Maseko",
    "Nandi Botha",
    "Pieter Jacobs",
    "Ayanda Naidoo",
    "Kabelo Radebe",
    "Fatima Khan",
    "Johan van Wyk",
    "Nomsa Molefe",
    "Sibusiso Zulu",
    "Chipo Ncube",
    "Michael Smith",
    "Priya Govender",
    "Tshepo Masego",
    "Refilwe Moletsane",
    "Andre du Plessis",
    "Boitumelo Mokoena",
    "Daniel Williams",
    "Sarah Adams",
    "Kagiso Morake",
    "Leah Petersen",
    "Mandisa Gumede",
    "Ruan Fourie",
    "Tumi Sebola",
]

FAILURE_REASONS = [
    "Insufficient funds",
    "Card declined",
    "Payment gateway timeout",
    "Velocity check triggered",
    "Account temporarily blocked",
    "Beneficiary bank unavailable",
    "Fraud rule match",
    "AML rule match",
    "Card expired",
    "Network processing error",
]

DAILY_VOLUMES = [7, 11, 9, 18, 14, 26, 21, 30, 27, 19, 33, 28, 35, 22]
FAILED_COUNTS = [1, 2, 1, 4, 2, 6, 4, 3, 7, 4, 8, 5, 6, 3]
PENDING_COUNTS = [1, 1, 2, 2, 3, 2, 4, 3, 2, 4, 3, 5, 4, 2]
WORKFLOW_COUNTS = [1, 2, 1, 3, 2, 4, 2, 5, 3, 2, 6, 4, 5, 3]
AUDIT_ERROR_COUNTS = [0, 1, 0, 2, 1, 3, 1, 2, 4, 1, 5, 2, 3, 1]


def create_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            risk_level TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
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
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_runs (
            workflow_id TEXT PRIMARY KEY,
            workflow_name TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            triggered_by_role TEXT NOT NULL,
            summary TEXT
        )
        """
    )
    conn.commit()


def seed_customers(cursor: sqlite3.Cursor) -> None:
    risk_levels = ["low", "medium", "high", "medium", "low"]
    customers = []
    for index, name in enumerate(CUSTOMER_NAMES, start=1):
        customer_id = f"CUST{index:03d}"
        email_name = name.lower().replace(" ", ".")
        customers.append((customer_id, name, f"{email_name}@example.com", risk_levels[index % len(risk_levels)]))

    cursor.executemany(
        """
        INSERT OR REPLACE INTO customers
        (customer_id, full_name, email, risk_level)
        VALUES (?, ?, ?, ?)
        """,
        customers,
    )


def seeded_amount(rng: random.Random, day_index: int, item_index: int, status: str) -> float:
    base = 180 + (day_index * 37) + (item_index * 19)
    multiplier = 1.0 if status == "successful" else 1.35 if status == "failed" else 0.72
    jitter = rng.uniform(35, 950)
    if item_index % 11 == 0:
        jitter += rng.uniform(1200, 4200)
    return round((base + jitter) * multiplier, 2)


def seed_transactions(cursor: sqlite3.Cursor) -> None:
    rng = random.Random(20260611)
    start_date = datetime(2026, 5, 28, 7, 35, 0)
    transaction_id = 1
    transactions = []

    for day_index, volume in enumerate(DAILY_VOLUMES):
        day = start_date + timedelta(days=day_index)
        statuses = (
            ["failed"] * FAILED_COUNTS[day_index]
            + ["pending"] * PENDING_COUNTS[day_index]
            + ["successful"] * (volume - FAILED_COUNTS[day_index] - PENDING_COUNTS[day_index])
        )
        rng.shuffle(statuses)

        for item_index, status in enumerate(statuses):
            minute_offset = int(((item_index + 1) * 37 + rng.randint(0, 26)) % 690)
            created_at = day + timedelta(minutes=minute_offset)
            customer_id = f"CUST{rng.randint(1, 30):03d}"
            failure_reason = rng.choice(FAILURE_REASONS) if status == "failed" else None
            transactions.append(
                (
                    f"TXN-DEMO-{transaction_id:04d}",
                    customer_id,
                    seeded_amount(rng, day_index, item_index, status),
                    "ZAR",
                    status,
                    failure_reason,
                    created_at.isoformat(timespec="seconds"),
                )
            )
            transaction_id += 1

    cursor.executemany(
        """
        INSERT OR REPLACE INTO transactions
        (transaction_id, customer_id, amount, currency, status, failure_reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        transactions,
    )


def seed_workflows(cursor: sqlite3.Cursor) -> None:
    start_date = datetime(2026, 5, 28, 8, 10, 0, tzinfo=timezone.utc)
    workflow_names = [
        "run_failed_transaction_incident_workflow",
        "generate_daily_ops_report",
        "export_failed_transactions_csv",
        "detect_failed_transaction_spike",
        "manual_review_queue_sync",
    ]
    statuses = ["completed", "completed", "completed", "no_action_required", "failed", "started"]
    roles = ["admin", "auditor", "finance_manager"]
    workflow_id = 1
    rows = []

    for day_index, count in enumerate(WORKFLOW_COUNTS):
        for item_index in range(count):
            started_at = start_date + timedelta(days=day_index, hours=item_index * 2, minutes=(day_index * 11 + item_index * 17) % 53)
            status = statuses[(day_index + item_index) % len(statuses)]
            completed_at = None
            if status not in {"started", "running"}:
                completed_at = (started_at + timedelta(minutes=2 + ((day_index + item_index) % 9))).isoformat()
            workflow_name = workflow_names[(day_index + item_index) % len(workflow_names)]
            rows.append(
                (
                    f"WF-DEMO-{workflow_id:04d}",
                    workflow_name,
                    status,
                    started_at.isoformat(),
                    completed_at,
                    roles[(day_index + item_index) % len(roles)],
                    f"Demo run for {workflow_name.replace('_', ' ')} on {started_at.date()}.",
                )
            )
            workflow_id += 1

    cursor.executemany(
        """
        INSERT OR REPLACE INTO workflow_runs
        (workflow_id, workflow_name, status, started_at, completed_at, triggered_by_role, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def seed_audit_log() -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_records = []
    if AUDIT_LOG_PATH.exists():
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not str(record.get("request_id", "")).startswith("REQ-DEMO-"):
                    existing_records.append(record)

    start_date = datetime(2026, 5, 28, 6, 45, 0, tzinfo=timezone.utc)
    tools = ["failed_transactions", "transaction_summary", "customer_payment_status", "search_audit_logs"]
    error_types = ["VALIDATION_ERROR", "ACCESS_DENIED", "RATE_LIMIT_EXCEEDED", "NOT_FOUND"]
    demo_records = []
    request_id = 1

    for day_index, volume in enumerate(DAILY_VOLUMES):
        success_count = max(3, volume // 4)
        error_count = AUDIT_ERROR_COUNTS[day_index]
        for item_index in range(success_count + error_count):
            is_error = item_index < error_count
            timestamp = start_date + timedelta(days=day_index, hours=1 + item_index, minutes=(day_index * 13 + item_index * 7) % 55)
            demo_records.append(
                {
                    "request_id": f"REQ-DEMO-{request_id:04d}",
                    "timestamp": timestamp.isoformat(),
                    "tool_name": tools[(day_index + item_index) % len(tools)],
                    "role": ["admin", "auditor", "support_agent"][(day_index + item_index) % 3],
                    "status": "error" if is_error else "success",
                    "error_type": error_types[(day_index + item_index) % len(error_types)] if is_error else None,
                    "input": {"demo": True, "date": str(timestamp.date())},
                    "output_preview": "Demo audit event for time-series dashboard trend.",
                    "execution_time_ms": 45 + ((day_index * 17 + item_index * 23) % 260),
                }
            )
            request_id += 1

    with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as file:
        for record in existing_records + demo_records:
            file.write(json.dumps(record) + "\n")


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        create_tables(conn)
        cursor = conn.cursor()
        seed_customers(cursor)
        seed_transactions(cursor)
        seed_workflows(cursor)
        conn.commit()
    seed_audit_log()
    print("Demo time-series data seeded successfully.")
    print(f"Database: {DB_PATH}")
    print(f"Audit log: {AUDIT_LOG_PATH}")


if __name__ == "__main__":
    main()
