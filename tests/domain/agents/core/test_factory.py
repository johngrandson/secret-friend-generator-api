from langchain_core.tools import tool

import src.domain.agents.core.factory as mod
from tests.domain.agents.core.conftest import ToolCapableFakeLLM


def test_make_agent_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    agent = mod.make_agent(name="test-agent", llm=fake_llm)
    assert callable(getattr(agent, "invoke", None))


def test_make_agent_with_tool(fake_llm: ToolCapableFakeLLM) -> None:
    @tool
    def dummy_tool(x: str) -> str:
        """Dummy tool for testing."""
        return x

    agent = mod.make_agent(name="tool-agent", llm=fake_llm, tools=[dummy_tool])
    assert callable(getattr(agent, "invoke", None))


def test_make_agent_with_system_prompt(fake_llm: ToolCapableFakeLLM) -> None:
    agent = mod.make_agent(
        name="prompted-agent",
        llm=fake_llm,
        system="You are a helpful assistant.",
    )
    assert callable(getattr(agent, "invoke", None))


def test_make_agent_no_tools_defaults_to_empty_list(
    fake_llm: ToolCapableFakeLLM,
) -> None:
    # Should not raise even when tools=None
    agent = mod.make_agent(name="bare-agent", llm=fake_llm, tools=None)
    assert callable(getattr(agent, "invoke", None))
