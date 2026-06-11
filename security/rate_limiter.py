from time import time
from typing import Any, TypeAlias


RateLimitRule: TypeAlias = dict[str, int]
RateLimitError: TypeAlias = dict[str, Any]


# In-memory rate limit store.
# Structure:
# {
#   ("support_agent", "customer_payment_status"): [timestamp1, timestamp2, ...]
# }
RATE_LIMIT_STORE: dict[tuple[str, str], list[float]] = {}


DEFAULT_RATE_LIMIT: RateLimitRule = {
    "limit": 10,
    "window_seconds": 60,
}


RATE_LIMIT_RULES: dict[str, dict[str, RateLimitRule]] = {
    "support_agent": {
        "customer_payment_status": {
            "limit": 5,
            "window_seconds": 60,
        },
        "open_support_ticket": {
            "limit": 3,
            "window_seconds": 60,
        },
    },

    "admin": {
        "failed_transactions": {
            "limit": 20,
            "window_seconds": 60,
        },
        "transaction_summary": {
            "limit": 20,
            "window_seconds": 60,
        },
        "customer_payment_status": {
            "limit": 20,
            "window_seconds": 60,
        },
        "open_support_ticket": {
            "limit": 10,
            "window_seconds": 60,
        },
        "audit_logs": {
            "limit": 15,
            "window_seconds": 60,
        },
        "search_audit_logs": {
            "limit": 15,
            "window_seconds": 60,
        },
        "detect_failed_transaction_spike": {
            "limit": 10,
            "window_seconds": 60,
        },
        "get_security_policy": {
            "limit": 10,
            "window_seconds": 60,
        },
        "get_workflow_runs": {
        "limit": 20,
        "window_seconds": 60,
        },
        "export_failed_transactions_csv": {
        "limit": 10,
        "window_seconds": 60,
        },
        "run_failed_transaction_incident_workflow": {
        "limit": 10,
        "window_seconds": 60,
        },
        "generate_daily_ops_report": {
        "limit": 10,
        "window_seconds": 60,

},
    },

    "auditor": {
        "audit_logs": {
            "limit": 10,
            "window_seconds": 60,
        },
        "search_audit_logs": {
            "limit": 10,
            "window_seconds": 60,
        },
        "get_security_policy": {
            "limit": 10,
            "window_seconds": 60,
        },
        "transaction_summary": {
            "limit": 10,
            "window_seconds": 60,
        },
        "customer_payment_status": {
            "limit": 10,
            "window_seconds": 60,
        },
        "get_workflow_runs": {
        "limit": 20,
        "window_seconds": 60,
        },
        
    },
}


def get_rate_limit_rule(role: str, tool_name: str) -> RateLimitRule:
    """
    Get the rate limit rule for a role/tool pair.
    If no specific rule exists, return the default rule.
    """
    role = role.strip().lower()
    tool_name = tool_name.strip()

    return RATE_LIMIT_RULES.get(role, {}).get(tool_name, DEFAULT_RATE_LIMIT)


def check_rate_limit(role: str, tool_name: str) -> RateLimitError | None:
    """
    Check whether the role/tool pair is still within its rate limit.

    Returns:
        None if allowed.
        A dictionary if rate limit is exceeded.
    """
    role = role.strip().lower()
    tool_name = tool_name.strip()

    rule = get_rate_limit_rule(role, tool_name)
    limit = rule["limit"]
    window_seconds = rule["window_seconds"]

    current_time = time()
    key = (role, tool_name)

    timestamps = RATE_LIMIT_STORE.get(key, [])

    # Keep only timestamps still inside the active window.
    active_timestamps = [
        timestamp
        for timestamp in timestamps
        if current_time - timestamp < window_seconds
    ]

    if len(active_timestamps) >= limit:
        retry_after_seconds = int(
            window_seconds - (current_time - active_timestamps[0])
        )

        RATE_LIMIT_STORE[key] = active_timestamps

        return {
            "message": (
                f"Rate limit exceeded for role '{role}' on tool '{tool_name}'. "
                "Try again later."
            ),
            "details": {
                "limit": limit,
                "window_seconds": window_seconds,
                "retry_after_seconds": max(retry_after_seconds, 1),
            }
        }

    active_timestamps.append(current_time)
    RATE_LIMIT_STORE[key] = active_timestamps

    return None
