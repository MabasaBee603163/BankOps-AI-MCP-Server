from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing each MCP tool call.
    Example: REQ-20260611-A8F32C
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = uuid4().hex[:6].upper()
    return f"REQ-{date_part}-{random_part}"


def success_response(
    tool_name: str,
    role: str,
    data: Any,
    request_id: str | None = None
) -> dict[str, Any]:
    """
    Standard success response used by all MCP tools.
    """
    if request_id is None:
        request_id = generate_request_id()

    return {
        "status": "success",
        "request_id": request_id,
        "tool": tool_name,
        "role": role,
        "data": data
    }


def error_response(
    tool_name: str,
    role: str,
    error_type: str,
    message: str,
    request_id: str | None = None,
    details: Any | None = None
) -> dict[str, Any]:
    """
    Standard error response used by all MCP tools.
    """
    if request_id is None:
        request_id = generate_request_id()

    response = {
        "status": "error",
        "request_id": request_id,
        "tool": tool_name,
        "role": role,
        "error_type": error_type,
        "message": message
    }

    if details is not None:
        response["details"] = details

    return response
    
