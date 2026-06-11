ROLE_PERMISSIONS = {
    "support_agent": [
        "customer_payment_status",
        "open_support_ticket",
    ],
    "finance_manager": [
        "failed_transactions",
        "transaction_summary",
        "customer_payment_status",
    ],
    "admin": [
        "failed_transactions",
        "transaction_summary",
        "customer_payment_status",
        "open_support_ticket",
        "audit_logs",
        "detect_failed_transaction_spike",
        "search_audit_logs",
        "get_security_policy",
        "generate_daily_ops_report",
        "export_failed_transactions_csv",
        "run_failed_transaction_incident_workflow",
        "get_workflow_runs",
        "generate_daily_ops_report",
        "export_failed_transactions_csv",
        "run_failed_transaction_incident_workflow",
    ],

    "auditor": [
        "transaction_summary",
        "audit_logs",
        "search_audit_logs",
        "customer_payment_status",
        "get_security_policy",
        "get_workflow_runs",
        
    ]
}

def can_access_tool(role: str, tool_name: str) -> bool:
    """
    Check if a given role has permission to execute a specific tool.
    
    Args:
        role: The user's role (e.g., 'support_agent', 'admin')
        tool_name: The name of the tool attempting to be accessed.
        
    Returns:
        True if access is allowed, False otherwise.
    """
    allowed_tools = ROLE_PERMISSIONS.get(role, [])
    return tool_name in allowed_tools

def deny_access(role: str, tool_name: str) -> dict:
    """
    Returns a standardized access denied response.
    """
    return {
        "status": "error",
        "message": f"Access Denied: Role '{role}' is not authorized to use '{tool_name}'."
    }
