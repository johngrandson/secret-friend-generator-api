"""Tests for the support app."""

from unittest.mock import patch

import src.domain.agents.apps.support as mod
from tests.domain.agents.apps.conftest import ToolCapableFakeLLM


def test_create_support_app_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_support_app()
    assert callable(getattr(app, "invoke", None))
