import csv
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from tools.transactions import get_failed_transactions
from tools.workflows import (
    start_workflow_run,
    complete_workflow_run,
    fail_workflow_run,
)


EXPORTS_DIR = Path(__file__).resolve().parent.parent / "exports"


def generate_export_id() -> str:
    """
    Generate a unique export ID.
    Example: EXPORT-20260610-A8F32C
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = uuid4().hex[:6].upper()
    return f"EXPORT-{date_part}-{random_part}"


def export_failed_transactions_csv(date: str, triggered_by_role: str = "admin"):
    """
    Export failed transactions for a given date into a CSV file.
    """
    workflow = start_workflow_run(
        workflow_name="export_failed_transactions_csv",
        triggered_by_role=triggered_by_role,
        summary=f"Started failed transaction CSV export for {date}."
    )

    workflow_id = workflow["workflow_id"]

    try:
        export_id = generate_export_id()
        failed_transactions = get_failed_transactions(date)
        rows_exported = len(failed_transactions)

        EXPORTS_DIR.mkdir(exist_ok=True)

        file_name = f"failed_transactions_{date}_{export_id}.csv"
        file_path = EXPORTS_DIR / file_name

        fieldnames = [
            "transaction_id",
            "customer_id",
            "amount",
            "currency",
            "failure_reason",
            "created_at",
        ]

        with open(file_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for transaction in failed_transactions:
                writer.writerow({
                    "transaction_id": transaction.get("transaction_id"),
                    "customer_id": transaction.get("customer_id"),
                    "amount": transaction.get("amount"),
                    "currency": transaction.get("currency"),
                    "failure_reason": transaction.get("failure_reason"),
                    "created_at": transaction.get("created_at"),
                })

        complete_workflow_run(
            workflow_id=workflow_id,
            summary=(
                f"Failed transactions CSV export completed for {date}. "
                f"Rows exported: {rows_exported}."
            )
        )

        return {
            "workflow_id": workflow_id,
            "export_id": export_id,
            "date": date,
            "rows_exported": rows_exported,
            "file_path": str(file_path)
        }

    except Exception as error:
        fail_workflow_run(
            workflow_id=workflow_id,
            summary=f"Failed to export failed transactions CSV: {str(error)}"
        )

        raise