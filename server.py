import json
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from tools.transactions import get_failed_transactions, get_transaction_summary
from tools.customers import get_customer_payment_status
from tools.tickets import create_support_ticket
from tools.audit import (
    log_tool_call,
    get_audit_logs,
    search_audit_logs as query_audit_logs,
)
from time import perf_counter

from security.permissions import can_access_tool, deny_access
from tools.automations import (
    detect_failed_transaction_spike as run_failed_transaction_spike_detection,
)
from security.masking import mask_customer_record_by_role
from security.validators import (
    validate_date,
    validate_customer_id,
    validate_priority,
    validate_text_field,
    validate_limit,
    validate_threshold,
    validate_optional_log_status,
    validate_optional_error_type,
    validate_optional_tool_name,
    validate_optional_role_filter,
    validate_optional_workflow_name,
    validate_optional_workflow_status,
    validate_optional_triggered_by_role,
)
from security.responses import (
    generate_request_id,
    success_response,
    error_response,
)
from security.security_policy import get_security_policy
from security.rate_limiter import check_rate_limit
from tools.workflows import get_recent_workflow_runs, search_workflow_runs
from tools.reports import generate_daily_ops_report
from tools.exports import export_failed_transactions_csv
from tools.incidents import run_failed_transaction_incident_workflow


mcp = FastMCP("BankOps MCP Server")


def _decode_wrapped_payload(value):
    """
    Some MCP clients can accidentally send the full JSON argument object as the
    date value. Decode that shape so the tool still receives the intended args.
    """
    if isinstance(value, dict):
        return value

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value.startswith("{") or not value.endswith("}"):
        return None

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def _normalize_date_tool_args(date, role):
    payload = _decode_wrapped_payload(date)

    if not payload:
        return date.strip() if isinstance(date, str) else date, role, {}

    normalized_date = payload.get("date", date)
    normalized_role = role

    if role == "support_agent" and "role" in payload:
        normalized_role = payload["role"]

    if isinstance(normalized_date, str):
        normalized_date = normalized_date.strip()

    if isinstance(normalized_role, str):
        normalized_role = normalized_role.strip()

    return normalized_date, normalized_role, payload


def _normalize_audit_search_args(
    tool_name,
    role_filter,
    status,
    error_type,
    limit,
    role
):
    args = {
        "tool_name": tool_name,
        "role_filter": role_filter,
        "status": status,
        "error_type": error_type,
        "limit": limit,
        "role": role,
    }

    for value in list(args.values()):
        payload = _decode_wrapped_payload(value)

        if not payload:
            continue

        for key in args:
            if key in payload:
                args[key] = payload[key]

    return (
        args["tool_name"],
        args["role_filter"],
        args["status"],
        args["error_type"],
        args["limit"],
        args["role"],
    )


def run_and_log(tool_name: str,func,input_data: dict,data_transform: Callable[[Any, str], Any] | None = None) -> dict[str, Any]:
    """
    Runs a tool function, checks permissions, wraps the response,
    measures execution time, and logs the tool call.
    """
    request_id = generate_request_id()
    start_time = perf_counter()

    role = input_data.pop("role", "support_agent")
    role = role.strip().lower()

    if not can_access_tool(role, tool_name):
        result = error_response(
            tool_name=tool_name,
            role=role,
            error_type="ACCESS_DENIED",
            message=f"Role '{role}' is not authorized to use '{tool_name}'.",
            request_id=request_id
        )

        execution_time_ms = int((perf_counter() - start_time) * 1000)

        log_tool_call(
            tool_name,
            {"request_id": request_id, "role": role, **input_data},
            result,
            execution_time_ms=execution_time_ms
        )

        return result

    rate_limit_error = check_rate_limit(role, tool_name)

    if rate_limit_error:
        result = error_response(
            tool_name=tool_name,
            role=role,
            error_type="RATE_LIMIT_EXCEEDED",
            message=rate_limit_error["message"],
            request_id=request_id,
            details=rate_limit_error["details"]
        )

        execution_time_ms = int((perf_counter() - start_time) * 1000)

        log_tool_call(
            tool_name,
            {"request_id": request_id, "role": role, **input_data},
            result,
            execution_time_ms=execution_time_ms
        )

        return result

    try:
        data = func(**input_data)

        if is_not_found_result(data):
            result = error_response(
                tool_name=tool_name,
                role=role,
                error_type="NOT_FOUND",
                message=data.get("error", "Requested record was not found."),
                request_id=request_id
        )
        else:
            result = success_response(
                tool_name=tool_name,
                role=role,
                data=data,
                request_id=request_id
            )

        execution_time_ms = int((perf_counter() - start_time) * 1000)

        log_tool_call(
            tool_name,
            {"request_id": request_id, "role": role, **input_data},
            result,
            execution_time_ms=execution_time_ms
        )

        return result

    except Exception as error:
        result = error_response(
            tool_name=tool_name,
            role=role,
            error_type="SYSTEM_ERROR",
            message="An unexpected system error occurred while running the tool.",
            request_id=request_id,
            details=str(error)
        )

        execution_time_ms = int((perf_counter() - start_time) * 1000)

        log_tool_call(
            tool_name,
            {"request_id": request_id, "role": role, **input_data},
            result,
            execution_time_ms=execution_time_ms
        )

        return result

def validation_failed(
    tool_name: str,
    role: str,
    message: str,
    details=None
) -> dict[str, Any]:
    """
    Create a standardized validation error response and log it.
    """
    request_id = generate_request_id()

    start_time = perf_counter()

    role = role.strip().lower()

    result = error_response(
        tool_name=tool_name,
        role=role,
        error_type="VALIDATION_ERROR",
        message=message,
        request_id=request_id,
        details=details
    )

    execution_time_ms = int((perf_counter() - start_time) * 1000)

    log_tool_call(
        tool_name,
        {
            "request_id": request_id,
            "role": role,
            "validation_failed": True,
            "details": details
        },
        result,
        execution_time_ms=execution_time_ms
    )

    return result

def is_not_found_result(data) -> bool:
    """
    Detect tool results that represent a not-found condition.
    """
    if not isinstance(data, dict):
        return False

    error_message = str(data.get("error", "")).lower()

    not_found_phrases = [
        "not found",
        "does not exist",
        "no record found",
    ]

    return any(phrase in error_message for phrase in not_found_phrases)

@mcp.tool()
def failed_transactions(date: str, role: str = "support_agent"):
    """
    Get failed bank transactions for a specific date.

    Args:
        date: Date in YYYY-MM-DD format.
        role: User role requesting access.
    """
    date, role, _ = _normalize_date_tool_args(date, role)
    validation_error = validate_date(date)

    if validation_error:
        return validation_failed(
            tool_name="failed_transactions",
            role=role,
            message=validation_error["message"],
            details={"date": date}
        )

    return run_and_log(
        "failed_transactions",
        get_failed_transactions,
        {
            "date": date,
            "role": role
        }
    )

@mcp.tool()
def transaction_summary(date: str, role: str = "support_agent"):
    """
    Get a transaction status summary for a specific date.

    Args:
        date: Date in YYYY-MM-DD format.
        role: User role requesting access.
    """
    date, role, _ = _normalize_date_tool_args(date, role)
    validation_error = validate_date(date)

    if validation_error:
        return validation_failed(
            tool_name="transaction_summary",
            role=role,
            message=validation_error["message"],
            details={"date": date}
        )

    return run_and_log(
        "transaction_summary",
        get_transaction_summary,
        {
            "date": date,
            "role": role
        }
    )

@mcp.tool()
def customer_payment_status(customer_id: str, role: str = "support_agent"):
    """
    Get the latest payment or transaction status for a customer.

    Args:
        customer_id: Customer ID, for example CUST002.
        role: User role requesting access.
    """
    role = role.strip().lower()
    customer_id = customer_id.strip().upper()

    validation_error = validate_customer_id(customer_id)

    if validation_error:
        return validation_failed(
            tool_name="customer_payment_status",
            role=role,
            message=validation_error["message"],
            details={"customer_id": customer_id}
        )

    return run_and_log(
        "customer_payment_status",
        get_customer_payment_status,
        {
            "customer_id": customer_id,
            "role": role
        },
        data_transform=mask_customer_record_by_role
    )

@mcp.tool()
def open_support_ticket(
    title: str,
    priority: str,
    description: str,
    role: str = "support_agent"
):
    """
    Create a support ticket for an operations issue.

    Args:
        title: Short ticket title.
        priority: One of low, medium, high, critical.
        description: Detailed issue description.
        role: User role requesting access.
    """
    priority = priority.strip().lower()

    title_error = validate_text_field("title", title, min_length=5, max_length=100)
    priority_error = validate_priority(priority)
    description_error = validate_text_field("description", description, min_length=10, max_length=500)

    if title_error:
        return validation_failed(
            tool_name="open_support_ticket",
            role=role,
            message=title_error["message"],
            details={"field": "title", "value": title}
        )

    if priority_error:
        return validation_failed(
            tool_name="open_support_ticket",
            role=role,
            message=priority_error["message"],
            details={"field": "priority", "value": priority}
        )

    if description_error:
        return validation_failed(
            tool_name="open_support_ticket",
            role=role,
            message=description_error["message"],
            details={"field": "description"}
        )

    return run_and_log(
        "open_support_ticket",
        create_support_ticket,
        {
            "title": title.strip(),
            "priority": priority,
            "description": description.strip(),
            "role": role
        }
    )

@mcp.tool()
def audit_logs(limit: int = 10, role: str = "support_agent"):
    """
    Get the latest MCP tool audit logs.

    Args:
        limit: Number of recent logs to return.
        role: User role requesting access.
    """
    validation_error = validate_limit(limit)

    if validation_error:
        return validation_failed(
            tool_name="audit_logs",
            role=role,
            message=validation_error["message"],
            details={"limit": limit}
        )

    return run_and_log(
        "audit_logs",
        get_audit_logs,
        {
            "limit": limit,
            "role": role
        }
    )

@mcp.tool()
def detect_failed_transaction_spike(
    date: str,
    threshold: int = 2,
    role: str = "support_agent"
):
    """
    Detect a failed transaction spike and automatically create a support ticket
    if failures meet or exceed the threshold.

    Args:
        date: Date in YYYY-MM-DD format.
        threshold: Number of failed transactions required to trigger an incident.
        role: User role requesting access.
    """
    date, role, payload = _normalize_date_tool_args(date, role)

    if "threshold" in payload:
        threshold = payload["threshold"]

    date_error = validate_date(date)
    threshold_error = validate_threshold(threshold)

    if date_error:
        return validation_failed(
            tool_name="detect_failed_transaction_spike",
            role=role,
            message=date_error["message"],
            details={"date": date}
        )

    if threshold_error:
        return validation_failed(
            tool_name="detect_failed_transaction_spike",
            role=role,
            message=threshold_error["message"],
            details={"threshold": threshold}
        )

    return run_and_log(
        "detect_failed_transaction_spike",
        run_failed_transaction_spike_detection,
        {
            "date": date,
            "threshold": threshold,
            "role": role
        }
    )
@mcp.tool()
def security_policy(role: str = "support_agent"):
    """
    Return the MCP server security and governance policy.

    Args:
        role: User role requesting access.
    """
    return run_and_log(
        "get_security_policy",
        get_security_policy,
        {
            "role": role
        }
    )
@mcp.tool()
def search_audit_logs(
    tool_name: str | None = None,
    role_filter: str | None = None,
    status: str | None = None,
    error_type: str | None = None,
    limit: int = 10,
    role: str = "support_agent"
):
    """
    Search audit logs by tool name, calling role, status, and error type.

    Args:
        tool_name: Optional MCP tool name to filter by.
        role_filter: Optional role to search for inside audit logs.
        status: Optional status filter: success or error.
        error_type: Optional error type filter, e.g. ACCESS_DENIED.
        limit: Maximum number of matching logs to return.
        role: User role requesting access.
    """
    (
        tool_name,
        role_filter,
        status,
        error_type,
        limit,
        role,
    ) = _normalize_audit_search_args(
        tool_name,
        role_filter,
        status,
        error_type,
        limit,
        role,
    )

    tool_name_error = validate_optional_tool_name(tool_name)
    role_filter_error = validate_optional_role_filter(role_filter)
    status_error = validate_optional_log_status(status)
    error_type_error = validate_optional_error_type(error_type)
    limit_error = validate_limit(limit)

    if tool_name_error:
        return validation_failed(
            tool_name="search_audit_logs",
            role=role,
            message=tool_name_error["message"],
            details={"tool_name": tool_name}
        )

    if role_filter_error:
        return validation_failed(
            tool_name="search_audit_logs",
            role=role,
            message=role_filter_error["message"],
            details={"role_filter": role_filter}
        )

    if status_error:
        return validation_failed(
            tool_name="search_audit_logs",
            role=role,
            message=status_error["message"],
            details={"status": status}
        )

    if error_type_error:
        return validation_failed(
            tool_name="search_audit_logs",
            role=role,
            message=error_type_error["message"],
            details={"error_type": error_type}
        )

    if limit_error:
        return validation_failed(
            tool_name="search_audit_logs",
            role=role,
            message=limit_error["message"],
            details={"limit": limit}
        )

    normalized_status = status.strip().lower() if status else None
    normalized_error_type = error_type.strip().upper() if error_type else None
    normalized_tool_name = tool_name.strip() if tool_name else None
    normalized_role_filter = role_filter.strip().lower() if role_filter else None

    return run_and_log(
        "search_audit_logs",
        query_audit_logs,
        {
            "tool_name": normalized_tool_name,
            "role_filter": normalized_role_filter,
            "status": normalized_status,
            "error_type": normalized_error_type,
            "limit": limit,
            "role": role
        }
    )

@mcp.tool()
def get_workflow_runs(
    workflow_name: str | None = None,
    status: str | None = None,
    triggered_by_role: str | None = None,
    limit: int = 10,
    role: str = "support_agent"
):
    """
    Search or list workflow run history.

    Args:
        workflow_name: Optional workflow name filter.
        status: Optional workflow status filter.
        triggered_by_role: Optional role that triggered the workflow.
        limit: Number of workflow runs to return.
        role: User role requesting access.
    """
    role = role.strip().lower()

    workflow_name_error = validate_optional_workflow_name(workflow_name)
    status_error = validate_optional_workflow_status(status)
    triggered_by_role_error = validate_optional_triggered_by_role(triggered_by_role)
    limit_error = validate_limit(limit)

    if workflow_name_error:
        return validation_failed(
            tool_name="get_workflow_runs",
            role=role,
            message=workflow_name_error["message"],
            details={"workflow_name": workflow_name}
        )

    if status_error:
        return validation_failed(
            tool_name="get_workflow_runs",
            role=role,
            message=status_error["message"],
            details={"status": status}
        )

    if triggered_by_role_error:
        return validation_failed(
            tool_name="get_workflow_runs",
            role=role,
            message=triggered_by_role_error["message"],
            details={"triggered_by_role": triggered_by_role}
        )

    if limit_error:
        return validation_failed(
            tool_name="get_workflow_runs",
            role=role,
            message=limit_error["message"],
            details={"limit": limit}
        )

    normalized_workflow_name = workflow_name.strip() if workflow_name else None
    normalized_status = status.strip().lower() if status else None
    normalized_triggered_by_role = triggered_by_role.strip().lower() if triggered_by_role else None

    return run_and_log(
        "get_workflow_runs",
        search_workflow_runs,
        {
            "workflow_name": normalized_workflow_name,
            "status": normalized_status,
            "triggered_by_role": normalized_triggered_by_role,
            "limit": limit,
            "role": role
        }
    )

@mcp.tool()
def failed_transactions_csv_export(date: str, role: str = "support_agent"):
    """
    Export failed transactions for a specific date to a CSV file.

    Args:
        date: Date in YYYY-MM-DD format.
        role: User role requesting access.
    """
    role = role.strip().lower()

    date_error = validate_date(date)

    if date_error:
        return validation_failed(
            tool_name="export_failed_transactions_csv",
            role=role,
            message=date_error["message"],
            details={"date": date}
        )

    return run_and_log(
        "export_failed_transactions_csv",
        export_failed_transactions_csv,
        {
            "date": date,
            "triggered_by_role": role,
            "role": role
        }
    )

@mcp.tool()
def failed_transaction_incident_workflow(
    date: str,
    threshold: int = 2,
    role: str = "support_agent"
):
    """
    Run the full failed transaction incident response workflow.

    Args:
        date: Date in YYYY-MM-DD format.
        threshold: Number of failed transactions required to trigger incident response.
        role: User role requesting access.
    """
    role = role.strip().lower()

    date_error = validate_date(date)
    threshold_error = validate_threshold(threshold)

    if date_error:
        return validation_failed(
            tool_name="run_failed_transaction_incident_workflow",
            role=role,
            message=date_error["message"],
            details={"date": date}
        )

    if threshold_error:
        return validation_failed(
            tool_name="run_failed_transaction_incident_workflow",
            role=role,
            message=threshold_error["message"],
            details={"threshold": threshold}
        )

    return run_and_log(
        "run_failed_transaction_incident_workflow",
        run_failed_transaction_incident_workflow,
        {
            "date": date,
            "threshold": threshold,
            "triggered_by_role": role,
            "role": role
        }
    )


@mcp.tool()
def daily_ops_report(date: str, role: str = "support_agent"):
    """
    Generate a daily banking operations report for a specific date.

    Args:
        date: Date in YYYY-MM-DD format.
        role: User role requesting access.
    """
    role = role.strip().lower()

    date_error = validate_date(date)

    if date_error:
        return validation_failed(
            tool_name="generate_daily_ops_report",
            role=role,
            message=date_error["message"],
            details={"date": date}
        )

    return run_and_log(
        "generate_daily_ops_report",
        generate_daily_ops_report,
        {
            "date": date,
            "triggered_by_role": role,
            "role": role
        }
    )

if __name__ == "__main__":
    mcp.run()
