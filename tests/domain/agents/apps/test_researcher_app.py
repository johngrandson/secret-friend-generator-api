"""Tests for the researcher app."""

from unittest.mock import patch

import src.domain.agents.apps.researcher_app as mod
from tests.domain.agents.apps.conftest import ToolCapableFakeLLM


def test_create_researcher_app_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_researcher_app()
    assert callable(getattr(app, "invoke", None))
