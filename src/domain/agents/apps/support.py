"""Support app — billing, tech support, and returns agents under a support router."""

from langgraph.graph.state import CompiledStateGraph

from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.core.supervisor import make_supervisor
from src.domain.agents.tools.support.billing import (
    check_balance,
    issue_refund,
    lookup_customer,
)
from src.domain.agents.tools.support.escalation import (
    escalate_to_human,
)
from src.domain.agents.tools.support.returns import initiate_return
from src.domain.agents.tools.support.tech import (
    create_ticket,
    list_tickets,
    lookup_order,
    search_orders,
)

_SUPPORT_PROMPT = (
    "You are a support router. "
    "Route billing and refund questions to billing_agent. "
    "Route technical issues, order lookups, and ticket management "
    "to tech_support_agent. "
    "Route return requests to returns_agent."
)


def create_support_app() -> CompiledStateGraph:
    """Build a supervisor graph with billing, tech support, and returns agents.

    Returns:
        Compiled supervisor graph with an ``invoke`` method.
    """
    llm = create_llm()

    billing_agent = make_agent(
        name="billing_agent",
        llm=llm,
        tools=[lookup_customer, check_balance, issue_refund, escalate_to_human],
        system=(
            "You are a billing specialist. "
            "Help customers with account lookups, balance inquiries, and refunds."
        ),
    )
    tech_support_agent = make_agent(
        name="tech_support_agent",
        llm=llm,
        tools=[
            lookup_order,
            search_orders,
            create_ticket,
            list_tickets,
            escalate_to_human,
        ],
        system=(
            "You are a technical support agent. "
            "Help customers with order status and support tickets."
        ),
    )
    returns_agent = make_agent(
        name="returns_agent",
        llm=llm,
        tools=[initiate_return, escalate_to_human],
        system=(
            "You are a returns specialist. "
            "Help customers initiate returns for delivered orders."
        ),
    )

    return make_supervisor(
        agents=[billing_agent, tech_support_agent, returns_agent],
        llm=llm,
        supervisor_name="support_router",
        prompt=_SUPPORT_PROMPT,
    )
