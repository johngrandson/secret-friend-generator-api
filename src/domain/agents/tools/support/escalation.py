"""Escalation tools for the support agent."""

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
async def escalate_to_human(reason: str, customer_id: str) -> str:
    """Escalate a support case to a human agent after approval.

    Args:
        reason: The reason for escalation.
        customer_id: The affected customer.

    Returns:
        Confirmation that escalation has been approved.
    """
    interrupt(
        {
            "action": "escalate_to_human",
            "customer_id": customer_id,
            "reason": reason,
        }
    )
    return (
        f"Case for customer {customer_id} has been escalated to a human agent: {reason}"
    )
