import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel


class ToolCapableFakeLLM(FakeListChatModel):
    """FakeListChatModel with a no-op bind_tools for unit tests.

    LangGraph internals call bind_tools when tools are present or when
    building supervisor/swarm graphs; base FakeListChatModel raises
    NotImplementedError, so we stub it here.
    """

    def bind_tools(self, tools, **kwargs):  # type: ignore[override]
        return self


@pytest.fixture
def fake_llm() -> ToolCapableFakeLLM:
    return ToolCapableFakeLLM(responses=["ok"])
