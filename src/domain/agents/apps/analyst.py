"""Analyst app — structured output agent using SummarySchema."""

from typing import Literal

from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.tools.local import echo


class SummarySchema(BaseModel):
    """Structured output schema for the analyst agent."""

    title: str = Field(description="A short title for the summary")
    key_points: list[str] = Field(description="Key points extracted")
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="Overall sentiment"
    )


def create_analyst_app() -> CompiledStateGraph:
    """Build an analyst agent that returns structured SummarySchema output.

    Returns:
        Compiled agent graph with an ``invoke`` method.
    """
    llm = create_llm()

    tools: list[BaseTool] = [echo]

    return make_agent(
        name="analyst",
        llm=llm,
        tools=tools,
        system=(
            "You are an analyst. Summarise the provided text and return a structured "
            "summary with a title, key points, and overall sentiment."
        ),
        response_format=SummarySchema,
    )
