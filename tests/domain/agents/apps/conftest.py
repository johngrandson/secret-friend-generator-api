"""Shared fixtures for agent app tests."""

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel


class ToolCapableFakeLLM(FakeListChatModel):
    """FakeListChatModel with a no-op bind_tools for unit tests."""

    def bind_tools(self, tools, **kwargs):  # type: ignore[override]
        return self


@pytest.fixture
def fake_llm() -> ToolCapableFakeLLM:
    return ToolCapableFakeLLM(responses=["ok"])
