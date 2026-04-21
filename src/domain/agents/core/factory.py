from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


def make_agent(
    name: str,
    llm: BaseChatModel,
    tools: list[BaseTool] | None = None,
    system: str | None = None,
    response_format: type[BaseModel] | None = None,
) -> CompiledStateGraph:
    """Create a ReAct agent using LangGraph's prebuilt factory.

    Args:
        name: Unique identifier for the agent node.
        llm: Chat model to use for reasoning.
        tools: Optional list of tools the agent can invoke.
        system: Optional system prompt string.
        response_format: Optional structured output type.

    Returns:
        Compiled LangGraph agent with an ``invoke`` method.
    """
    kwargs: dict[str, Any] = {"name": name, "model": llm, "tools": tools or []}
    if system:
        kwargs["system_prompt"] = system
    if response_format:
        kwargs["response_format"] = response_format
    return create_agent(**kwargs)
