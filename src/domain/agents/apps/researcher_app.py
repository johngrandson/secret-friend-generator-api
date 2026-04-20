"""Researcher app — researcher + writer under a research coordination supervisor."""

from langgraph.graph.state import CompiledStateGraph

from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.core.supervisor import make_supervisor
from src.domain.agents.tools.local_tools import echo
from src.domain.agents.tools.web_tools import scrape_url, web_search

_RESEARCH_PROMPT = (
    "You coordinate research tasks. "
    "Send web research and scraping tasks to researcher. "
    "Send writing and summarisation tasks to writer. "
    "Always gather information before writing."
)


def create_researcher_app() -> CompiledStateGraph:
    """Build a supervisor graph with researcher and writer agents.

    Returns:
        Compiled supervisor graph with an ``invoke`` method.
    """
    llm = create_llm()

    researcher = make_agent(
        name="researcher",
        llm=llm,
        tools=[web_search, scrape_url],
        system=(
            "You are a researcher. "
            "Search the web and scrape URLs to gather information."
        ),
    )
    writer = make_agent(
        name="writer",
        llm=llm,
        tools=[echo],
        system=(
            "You are a writer. "
            "Compose clear, well-structured content from provided research."
        ),
    )

    return make_supervisor(
        agents=[researcher, writer],
        llm=llm,
        supervisor_name="research_supervisor",
        prompt=_RESEARCH_PROMPT,
    )
