from tools.transactions import get_failed_transactions, get_transaction_summary
from tools.customers import get_customer_payment_status
from tools.tickets import create_support_ticket
from tools.audit import log_tool_call, get_audit_logs


def run_tool(tool_name, func, input_data):
    result = func(**input_data)
    log_tool_call(tool_name, input_data, result)
    return result


print("\nFAILED TRANSACTIONS")
print(run_tool(
    "get_failed_transactions",
    get_failed_transactions,
    {"date": "2026-06-10"}
))

print("\nTRANSACTION SUMMARY")
print(run_tool(
    "get_transaction_summary",
    get_transaction_summary,
    {"date": "2026-06-10"}
))

print("\nCUSTOMER PAYMENT STATUS")
print(run_tool(
    "get_customer_payment_status",
    get_customer_payment_status,
    {"customer_id": "CUST002"}
))

print("\nCREATE SUPPORT TICKET")
print(run_tool(
    "create_support_ticket",
    create_support_ticket,
    {
        "title": "High failed transaction count detected",
        "priority": "high",
        "description": "Multiple failed transactions were detected for 2026-06-10."
    }
))

print("\nAUDIT LOGS")
print(get_audit_logs(limit=5))