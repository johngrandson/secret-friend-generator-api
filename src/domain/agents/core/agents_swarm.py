from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph_swarm import create_swarm

from src.domain.agents.config.agents_checkpointer import get_checkpointer


def make_swarm(agents: list[Any], default_active_agent: str) -> CompiledStateGraph:
    """Build and compile a swarm graph where agents hand off to each other.

    Args:
        agents: Agent instances participating in the swarm.
        default_active_agent: Name of the agent that handles the first message.

    Returns:
        Compiled LangGraph swarm with ``invoke`` / ``stream`` methods.
    """
    graph = create_swarm(agents=agents, default_active_agent=default_active_agent)
    return graph.compile(checkpointer=get_checkpointer())
