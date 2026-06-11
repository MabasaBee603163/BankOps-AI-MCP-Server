from security.permissions import ROLE_PERMISSIONS
from security.rate_limiter import DEFAULT_RATE_LIMIT, RATE_LIMIT_RULES


def get_security_policy():
    """
    Return the current MCP server security policy.

    This is a read-only governance tool used to explain:
    - roles
    - tool permissions
    - active security controls
    """

    return {
        "roles": {
            role: sorted(list(tools))
            for role, tools in ROLE_PERMISSIONS.items()
        },
        "security_controls": [
            "role-based access control",
            "input validation",
            "standardized success and error responses",
            "request ID tracing",
            "structured audit logging",
            "audit log search",
            "role-based sensitive data masking",
            "masked audit output previews",
            "rate limiting",
        ],
        "rate_limiting": {
            "default": DEFAULT_RATE_LIMIT,
            "rules": RATE_LIMIT_RULES,
        },
        "data_protection": {
            "customer_data": {
                "support_agent": "partial masking",
                "admin": "full access",
                "auditor": "identity masked"
            },
            "audit_logs": "audit output previews must not expose unmasked sensitive customer data"
        },
        "policy_notes": [
            "The LLM cannot execute arbitrary SQL.",
            "The LLM can only call predefined MCP tools.",
            "Sensitive customer fields are masked according to role.",
            "Every MCP tool call receives a request ID.",
            "Every allowed, denied, validation-failed, and rate-limited request is logged."
        ]
    }
