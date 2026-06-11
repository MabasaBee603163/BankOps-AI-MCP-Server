import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from tools.transactions import get_failed_transactions
from tools.tickets import create_support_ticket
from tools.workflows import (
    start_workflow_run,
    complete_workflow_run,
    fail_workflow_run,
    mark_workflow_no_action_required,
)


REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def generate_incident_report_id() -> str:
    """
    Generate a unique incident report ID.
    Example: INCIDENT-20260610-A8F32C
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = uuid4().hex[:6].upper()
    return f"INCIDENT-{date_part}-{random_part}"


def run_failed_transaction_incident_workflow(
    date: str,
    threshold: int = 2,
    triggered_by_role: str = "admin"
):
    """
    Run a full failed transaction incident response workflow.

    This workflow:
    - checks failed transactions
    - compares failure count to threshold
    - creates a support ticket if needed
    - generates an incident report
    - updates workflow run status
    """
    workflow = start_workflow_run(
        workflow_name="run_failed_transaction_incident_workflow",
        triggered_by_role=triggered_by_role,
        summary=f"Started failed transaction incident workflow for {date}."
    )

    workflow_id = workflow["workflow_id"]

    try:
        failed_transactions = get_failed_transactions(date)
        failed_count = len(failed_transactions)

        if failed_count < threshold:
            summary = (
                f"No incident required for {date}. "
                f"Failed transactions: {failed_count}. Threshold: {threshold}."
            )

            mark_workflow_no_action_required(
                workflow_id=workflow_id,
                summary=summary
            )

            return {
                "workflow_id": workflow_id,
                "incident_detected": False,
                "date": date,
                "threshold": threshold,
                "failed_count": failed_count,
                "workflow_status": "no_action_required",
                "message": "Failed transaction count is below threshold."
            }

        ticket = create_support_ticket(
            title=f"Failed transaction incident detected on {date}",
            priority="high",
            description=(
                f"{failed_count} failed transactions were detected on {date}. "
                f"This meets or exceeds the incident threshold of {threshold}. "
                "Operations team should investigate payment gateway, card processing, "
                "customer account, or banking network issues."
            )
        )

        incident_report_id = generate_incident_report_id()
        generated_at = datetime.now(timezone.utc).isoformat()

        incident_report = {
            "incident_report_id": incident_report_id,
            "workflow_id": workflow_id,
            "report_type": "failed_transaction_incident",
            "date": date,
            "generated_at": generated_at,
            "generated_by_role": triggered_by_role,
            "threshold": threshold,
            "failed_count": failed_count,
            "incident_detected": True,
            "ticket": ticket,
            "failed_transactions": failed_transactions,
            "recommended_actions": [
                "Review failed transaction error patterns.",
                "Check payment gateway health.",
                "Check whether failures are concentrated on specific customers or cards.",
                "Escalate to banking operations if failure rate continues increasing."
            ]
        }

        REPORTS_DIR.mkdir(exist_ok=True)

        file_name = f"incident_failed_transactions_{date}_{incident_report_id}.json"
        report_path = REPORTS_DIR / file_name

        with open(report_path, "w", encoding="utf-8") as file:
            json.dump(incident_report, file, indent=2)

        complete_workflow_run(
            workflow_id=workflow_id,
            summary=(
                f"Incident workflow completed for {date}. "
                f"Failed transactions: {failed_count}. "
                f"Ticket: {ticket.get('ticket_id')}."
            )
        )

        return {
            "workflow_id": workflow_id,
            "incident_report_id": incident_report_id,
            "incident_detected": True,
            "date": date,
            "threshold": threshold,
            "failed_count": failed_count,
            "ticket_created": ticket,
            "incident_report_path": str(report_path),
            "workflow_status": "completed"
        }

    except Exception as error:
        fail_workflow_run(
            workflow_id=workflow_id,
            summary=f"Incident workflow failed: {str(error)}"
        )

        raise