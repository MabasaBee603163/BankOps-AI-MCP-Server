import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "audit_log.jsonl"
SENSITIVE_AUDIT_FIELDS = {"email", "full_name"}
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
FULL_NAME_FIELD_PATTERN = re.compile(
    r"((?:'|\")full_name(?:'|\")\s*:\s*)(?:'[^']*'|\"[^\"]*\")"
)


def _redact_sensitive_text(value: str) -> str:
    value = EMAIL_PATTERN.sub("MASKED_EMAIL", value)
    return FULL_NAME_FIELD_PATTERN.sub(r"\1'MASKED'", value)


def _sanitize_for_audit(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "MASKED"
            if str(key).lower() in SENSITIVE_AUDIT_FIELDS
            else _sanitize_for_audit(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_sanitize_for_audit(item) for item in value]

    if isinstance(value, str):
        return _redact_sensitive_text(value)

    return value


def _sanitize_dict_for_audit(value: dict[str, Any]) -> dict[str, Any]:
    sanitized = _sanitize_for_audit(value)

    if isinstance(sanitized, dict):
        return sanitized

    return {}


def _load_audit_entry(line: str) -> dict[str, Any] | None:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return None

    if not isinstance(entry, dict):
        return None

    return entry


def log_tool_call(
    tool_name: str,
    input_data: dict[str, Any],
    output_data: Any,
    execution_time_ms: int | None = None
) -> None:
    """
    Log every MCP tool call as a structured JSONL audit event.

    Each line in audit_log.jsonl is one JSON object.
    This makes the logs easy to search, filter, and export later.
    """
    LOG_PATH.parent.mkdir(exist_ok=True)

    request_id = input_data.get("request_id")
    role = input_data.get("role", "unknown")

    status = None
    error_type = None

    if isinstance(output_data, dict):
        status = output_data.get("status")
        error_type = output_data.get("error_type")

        if request_id is None:
            request_id = output_data.get("request_id")

        if role == "unknown":
            role = output_data.get("role", "unknown")

    safe_input = _sanitize_dict_for_audit(input_data)
    safe_output = _sanitize_for_audit(output_data)
    output_preview = _redact_sensitive_text(str(safe_output))[:500]

    log_entry = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "role": role,
        "status": status,
        "error_type": error_type,
        "input": {
            key: value
            for key, value in safe_input.items()
            if key not in {"request_id", "role"}
        },
        "output_preview": output_preview,
        "execution_time_ms": execution_time_ms
    }

    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")


def get_audit_logs(limit: int = 10) -> list[dict[str, Any]]:
    """
    Return the latest audit log entries.
    """
    if not LOG_PATH.exists():
        return []

    with open(LOG_PATH, "r", encoding="utf-8") as file:
        lines = file.readlines()

    latest_lines = lines[-limit:]

    entries: list[dict[str, Any]] = []

    for line in latest_lines:
        entry = _load_audit_entry(line)

        if entry is not None:
            entries.append(_sanitize_dict_for_audit(entry))

    return entries

def search_audit_logs(
    tool_name: str | None = None,
    role_filter: str | None = None,
    status: str | None = None,
    error_type: str | None = None,
    limit: int = 10
) -> list[dict[str, Any]]:
    """
    Search audit logs by tool name, role, status, and error type.

    Args:
        tool_name: Filter by MCP tool name.
        role_filter: Filter by the role that called the tool.
        status: Filter by success or error.
        error_type: Filter by error type, e.g. ACCESS_DENIED.
        limit: Maximum number of matching results.
    """
    if not LOG_PATH.exists():
        return []

    with open(LOG_PATH, "r", encoding="utf-8") as file:
        lines = file.readlines()

    results: list[dict[str, Any]] = []

    for line in reversed(lines):
        entry = _load_audit_entry(line)

        if entry is None:
            continue

        if tool_name and entry.get("tool_name") != tool_name:
            continue

        if role_filter and entry.get("role") != role_filter:
            continue

        if status and entry.get("status") != status:
            continue

        if error_type and entry.get("error_type") != error_type:
            continue

        results.append(_sanitize_dict_for_audit(entry))

        if len(results) >= limit:
            break

    return results
