from datetime import datetime


ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}


def validate_date(date: str):
    """
    Validate date format: YYYY-MM-DD.
    """
    if not isinstance(date, str):
        return {
            "status": "error",
            "message": "date must be a string in YYYY-MM-DD format."
        }

    try:
        datetime.strptime(date.strip(), "%Y-%m-%d")
        return None
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date format. Use YYYY-MM-DD."
        }


def validate_customer_id(customer_id: str):
    """
    Validate customer ID format.
    Expected format: CUST001, CUST002, etc.
    """
    if not isinstance(customer_id, str):
        return {
            "status": "error",
            "message": "customer_id must be a string."
        }

    customer_id = customer_id.strip().upper()

    if not customer_id.startswith("CUST"):
        return {
            "status": "error",
            "message": "Invalid customer_id. It must start with 'CUST'."
        }

    if len(customer_id) != 7:
        return {
            "status": "error",
            "message": "Invalid customer_id length. Example format: CUST001."
        }

    if not customer_id[4:].isdigit():
        return {
            "status": "error",
            "message": "Invalid customer_id number. Example format: CUST001."
        }

    return None


def validate_priority(priority: str):
    """
    Validate support ticket priority.
    """
    if not isinstance(priority, str):
        return {
            "status": "error",
            "message": "priority must be a string."
        }

    priority = priority.strip().lower()

    if priority not in ALLOWED_PRIORITIES:
        return {
            "status": "error",
            "message": f"Invalid priority. Allowed values: {sorted(ALLOWED_PRIORITIES)}."
        }

    return None


def validate_text_field(field_name: str, value: str, min_length: int = 3, max_length: int = 200):
    """
    Validate basic text fields like title and description.
    """
    if not isinstance(value, str):
        return {
            "status": "error",
            "message": f"{field_name} must be a string."
        }

    value = value.strip()

    if len(value) < min_length:
        return {
            "status": "error",
            "message": f"{field_name} is too short. Minimum length is {min_length} characters."
        }

    if len(value) > max_length:
        return {
            "status": "error",
            "message": f"{field_name} is too long. Maximum length is {max_length} characters."
        }

    return None


def validate_limit(limit: int):
    """
    Validate audit log limit.
    """
    if not isinstance(limit, int):
        return {
            "status": "error",
            "message": "limit must be an integer."
        }

    if limit < 1:
        return {
            "status": "error",
            "message": "limit must be at least 1."
        }

    if limit > 50:
        return {
            "status": "error",
            "message": "limit cannot be greater than 50."
        }

    return None
    
def validate_threshold(threshold: int):
    """
    Validate automation threshold.
    """
    if not isinstance(threshold, int):
        return {
            "status": "error",
            "message": "threshold must be an integer."
        }

    if threshold < 1:
        return {
            "status": "error",
            "message": "threshold must be at least 1."
        }

    if threshold > 100:
        return {
            "status": "error",
            "message": "threshold cannot be greater than 100."
        }

    return None
ALLOWED_LOG_STATUSES = {"success", "error"}
ALLOWED_ERROR_TYPES = {
    "VALIDATION_ERROR",
    "ACCESS_DENIED",
    "NOT_FOUND",
    "DATABASE_ERROR",
    "SYSTEM_ERROR",
    "RATE_LIMIT_EXCEEDED",
}


def validate_optional_log_status(status: str | None):
    """
    Validate optional audit log status filter.
    """
    if status is None:
        return None

    if not isinstance(status, str):
        return {
            "status": "error",
            "message": "status must be a string."
        }

    status = status.strip().lower()

    if status not in ALLOWED_LOG_STATUSES:
        return {
            "status": "error",
            "message": f"Invalid status. Allowed values: {sorted(ALLOWED_LOG_STATUSES)}."
        }

    return None


def validate_optional_error_type(error_type: str | None):
    """
    Validate optional audit log error type filter.
    """
    if error_type is None:
        return None

    if not isinstance(error_type, str):
        return {
            "status": "error",
            "message": "error_type must be a string."
        }

    error_type = error_type.strip().upper()

    if error_type not in ALLOWED_ERROR_TYPES:
        return {
            "status": "error",
            "message": f"Invalid error_type. Allowed values: {sorted(ALLOWED_ERROR_TYPES)}."
        }

    return None


def validate_optional_tool_name(tool_name: str | None):
    """
    Validate optional audit tool_name filter.
    """
    if tool_name is None:
        return None

    if not isinstance(tool_name, str):
        return {
            "status": "error",
            "message": "tool_name must be a string."
        }

    if len(tool_name.strip()) < 2:
        return {
            "status": "error",
            "message": "tool_name filter is too short."
        }

    return None


def validate_optional_role_filter(role_filter: str | None):
    """
    Validate optional role filter for audit search.
    """
    if role_filter is None:
        return None

    if not isinstance(role_filter, str):
        return {
            "status": "error",
            "message": "role_filter must be a string."
        }

    if len(role_filter.strip()) < 2:
        return {
            "status": "error",
            "message": "role_filter is too short."
        }

    return None

ALLOWED_WORKFLOW_STATUSES = {
    "started",
    "completed",
    "failed",
    "no_action_required",
}


def validate_optional_workflow_name(workflow_name: str | None):
    """
    Validate optional workflow name filter.
    """
    if workflow_name is None:
        return None

    if not isinstance(workflow_name, str):
        return {
            "status": "error",
            "message": "workflow_name must be a string."
        }

    if len(workflow_name.strip()) < 3:
        return {
            "status": "error",
            "message": "workflow_name filter is too short."
        }

    return None


def validate_optional_workflow_status(status: str | None):
    """
    Validate optional workflow status filter.
    """
    if status is None:
        return None

    if not isinstance(status, str):
        return {
            "status": "error",
            "message": "workflow status must be a string."
        }

    status = status.strip().lower()

    if status not in ALLOWED_WORKFLOW_STATUSES:
        return {
            "status": "error",
            "message": f"Invalid workflow status. Allowed values: {sorted(ALLOWED_WORKFLOW_STATUSES)}."
        }

    return None


def validate_optional_triggered_by_role(triggered_by_role: str | None):
    """
    Validate optional triggered_by_role filter.
    """
    if triggered_by_role is None:
        return None

    if not isinstance(triggered_by_role, str):
        return {
            "status": "error",
            "message": "triggered_by_role must be a string."
        }

    if len(triggered_by_role.strip()) < 2:
        return {
            "status": "error",
            "message": "triggered_by_role filter is too short."
        }

    return None