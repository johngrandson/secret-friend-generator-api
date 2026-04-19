from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
from langgraph_supervisor import create_supervisor

from src.domain.agents.config.agents_checkpointer import get_checkpointer, get_store


def make_supervisor(
    agents: list[Any],
    llm: BaseChatModel,
    output_mode: str = "last_message",
    supervisor_name: str = "supervisor",
    prompt: str | None = None,
) -> CompiledStateGraph:
    """Build and compile a supervisor graph over a set of worker agents.

    Args:
        agents: Worker agent instances to supervise.
        llm: Chat model used by the supervisor node.
        output_mode: How the supervisor surfaces results.
            Either ``last_message`` or ``full_history``.
        supervisor_name: Name of the supervisor node in the graph.
        prompt: Optional system prompt for the supervisor.

    Returns:
        Compiled LangGraph supervisor with ``invoke`` / ``stream`` methods.
    """
    kwargs: dict[str, Any] = {
        "agents": agents,
        "model": llm,
        "output_mode": output_mode,
        "supervisor_name": supervisor_name,
    }
    if prompt:
        kwargs["prompt"] = prompt
    workflow = create_supervisor(**kwargs)
    return workflow.compile(checkpointer=get_checkpointer(), store=get_store())
