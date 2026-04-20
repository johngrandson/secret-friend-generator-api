"""Billing-related tools for the support agent."""

import json

from langchain_core.tools import tool
from langgraph.types import interrupt

from src.domain.agents.tools.support.mock_data import CUSTOMERS, ORDERS


@tool
async def lookup_customer(customer_id: str) -> str:
    """Look up a customer record by ID.

    Args:
        customer_id: The unique customer identifier (e.g. C-1001).

    Returns:
        JSON string of customer data, or a not-found message.
    """
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return f"Customer {customer_id} not found."
    return json.dumps({"customer_id": customer_id, **customer})


@tool
async def check_balance(customer_id: str) -> str:
    """Check the outstanding balance for a customer.

    Args:
        customer_id: The unique customer identifier.

    Returns:
        Human-readable balance description.
    """
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return f"Customer {customer_id} not found."
    balance: float = customer["balance"]
    if balance == 0:
        return f"Customer {customer_id} has no outstanding balance."
    return f"Customer {customer_id} has an outstanding balance of ${balance:.2f}."


@tool
async def issue_refund(order_id: str, reason: str) -> str:
    """Issue a refund for an order after human approval.

    Args:
        order_id: The order to refund.
        reason: The reason for the refund.

    Returns:
        Confirmation message after approval.
    """
    order = ORDERS.get(order_id)
    if order is None:
        return f"Order {order_id} not found."
    interrupt(
        {
            "action": "issue_refund",
            "order_id": order_id,
            "amount": order["total"],
            "reason": reason,
        }
    )
    return (
        f"Refund of ${order['total']:.2f} for order {order_id} "
        "has been approved and processed."
    )
