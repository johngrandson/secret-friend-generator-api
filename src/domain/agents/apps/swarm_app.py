"""Swarm app — alice and bob hand off to each other."""

from typing import Any

from langgraph.graph.state import CompiledStateGraph

from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.core.handoff import create_handoff_tool
from src.domain.agents.core.swarm import make_swarm
from src.domain.agents.tools.local_tools import add, echo, multiply


def create_swarm_app(mcp_tools: list[Any] | None = None) -> CompiledStateGraph:
    """Build a swarm graph where alice and bob hand off to each other.

    alice handles addition and can hand off to bob.
    bob handles multiplication and echo and can hand off to alice.

    Args:
        mcp_tools: Optional extra MCP tools appended to both agents.

    Returns:
        Compiled swarm graph with an ``invoke`` method.
    """
    extra = mcp_tools or []
    llm = create_llm()

    alice = make_agent(
        name="alice",
        llm=llm,
        tools=[add, create_handoff_tool(agent_name="bob"), *extra],
        system="You are Alice. Use add for math. Hand off to bob when needed.",
    )
    bob = make_agent(
        name="bob",
        llm=llm,
        tools=[multiply, echo, create_handoff_tool(agent_name="alice"), *extra],
        system="You are Bob. Use multiply or echo. Hand off to alice when needed.",
    )

    return make_swarm(agents=[alice, bob], default_active_agent="alice")
