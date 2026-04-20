"""Supervisor app — math_expert + writer coordinated by a supervisor."""

from typing import Any

from langgraph.graph.state import CompiledStateGraph

from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.core.supervisor import make_supervisor
from src.domain.agents.tools.local import add, echo, multiply


def create_supervisor_app(mcp_tools: list[Any] | None = None) -> CompiledStateGraph:
    """Build a supervisor graph with math_expert and writer agents.

    Args:
        mcp_tools: Optional extra MCP tools appended to both agents.

    Returns:
        Compiled supervisor graph with an ``invoke`` method.
    """
    extra = mcp_tools or []
    llm = create_llm()

    math_expert = make_agent(
        name="math_expert",
        llm=llm,
        tools=[add, multiply, *extra],
        system=(
            "You are a math expert. "
            "Use the add and multiply tools to answer calculations."
        ),
    )
    writer = make_agent(
        name="writer",
        llm=llm,
        tools=[echo, *extra],
        system="You are a writer. Use the echo tool to repeat content back.",
    )

    return make_supervisor(
        agents=[math_expert, writer],
        llm=llm,
        supervisor_name="supervisor",
        prompt=(
            "Route math questions to math_expert "
            "and writing tasks to writer."
        ),
    )
