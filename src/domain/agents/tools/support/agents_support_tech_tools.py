"""Tech-support tools for the support agent (orders + tickets)."""

import json
import uuid

from langchain_core.tools import tool

from src.domain.agents.tools.support.agents_support_mock_data import ORDERS, TICKETS


@tool
async def lookup_order(order_id: str) -> str:
    """Look up an order by its ID.

    Args:
        order_id: The unique order identifier (e.g. ORD-501).

    Returns:
        JSON string of order data, or a not-found message.
    """
    order = ORDERS.get(order_id)
    if order is None:
        return f"Order {order_id} not found."
    return json.dumps({"order_id": order_id, **order})


@tool
async def search_orders(customer_id: str) -> str:
    """Search all orders belonging to a customer.

    Args:
        customer_id: The customer whose orders to retrieve.

    Returns:
        JSON string listing all matching orders, or a not-found message.
    """
    results = [
        {"order_id": oid, **data}
        for oid, data in ORDERS.items()
        if data["customer_id"] == customer_id
    ]
    if not results:
        return f"No orders found for customer {customer_id}."
    return json.dumps(results)


@tool
async def create_ticket(customer_id: str, issue: str) -> str:
    """Create a new support ticket for a customer.

    Args:
        customer_id: The customer filing the ticket.
        issue: Description of the issue.

    Returns:
        Confirmation with the new ticket ID.
    """
    ticket_id = f"TK-{uuid.uuid4().hex[:6].upper()}"
    ticket: dict = {
        "id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "status": "open",
    }
    TICKETS.append(ticket)
    return f"Ticket {ticket_id} created for customer {customer_id}: {issue}"


@tool
async def list_tickets(customer_id: str) -> str:
    """List all support tickets for a customer.

    Args:
        customer_id: The customer whose tickets to list.

    Returns:
        JSON string of matching tickets, or a not-found message.
    """
    results = [t for t in TICKETS if t["customer_id"] == customer_id]
    if not results:
        return f"No tickets found for customer {customer_id}."
    return json.dumps(results)
