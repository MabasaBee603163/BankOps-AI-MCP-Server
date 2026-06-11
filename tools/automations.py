from tools.transactions import get_failed_transactions
from tools.tickets import create_support_ticket


def detect_failed_transaction_spike(date: str, threshold: int = 2):
    """
    Detect whether failed transactions exceed a given threshold.

    If the number of failed transactions is greater than or equal to the threshold,
    automatically create a support ticket.
    """
    failed_transactions = get_failed_transactions(date)
    failed_count = len(failed_transactions)

    if failed_count >= threshold:
        ticket = create_support_ticket(
            title=f"Failed transaction spike detected on {date}",
            priority="high",
            description=(
                f"{failed_count} failed transactions were detected on {date}. "
                f"This meets or exceeds the configured threshold of {threshold}. "
                "Operations team should investigate payment gateway, customer account, or card failure issues."
            )
        )

        return {
            "incident_detected": True,
            "date": date,
            "threshold": threshold,
            "failed_count": failed_count,
            "failed_transactions": failed_transactions,
            "ticket_created": ticket
        }

    return {
        "incident_detected": False,
        "date": date,
        "threshold": threshold,
        "failed_count": failed_count,
        "message": "No failed transaction spike detected."
    }