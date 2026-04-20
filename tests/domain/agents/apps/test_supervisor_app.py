"""Tests for the supervisor app."""

from unittest.mock import patch

import src.domain.agents.apps.supervisor_app as mod
from tests.domain.agents.apps.conftest import ToolCapableFakeLLM


def test_create_supervisor_app_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_supervisor_app()
    assert callable(getattr(app, "invoke", None))


def test_create_supervisor_app_with_mcp_tools(fake_llm: ToolCapableFakeLLM) -> None:
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_supervisor_app(mcp_tools=[])
    assert callable(getattr(app, "invoke", None))
