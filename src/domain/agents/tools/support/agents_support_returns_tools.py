"""Returns tools for the support agent."""

from langchain_core.tools import tool
from langgraph.types import interrupt

from src.domain.agents.tools.support.agents_support_mock_data import ORDERS


@tool
async def initiate_return(order_id: str, reason: str) -> str:
    """Initiate a return for a delivered order after human approval.

    Args:
        order_id: The order to return.
        reason: The reason for the return.

    Returns:
        Confirmation message after approval.
    """
    order = ORDERS.get(order_id)
    if order is None:
        return f"Order {order_id} not found."
    if order["status"] != "delivered":
        status = order["status"]
        return (
            f"Order {order_id} cannot be returned "
            f"— current status is '{status}'."
        )
    interrupt(
        {
            "action": "initiate_return",
            "order_id": order_id,
            "item": order["item"],
            "reason": reason,
        }
    )
    item = order["item"]
    return f"Return for order {order_id} ({item}) has been approved and initiated."
