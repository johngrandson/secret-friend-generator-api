"""Tests for the analyst app (structured output)."""

from unittest.mock import patch

import src.domain.agents.apps.analyst_app as mod
from tests.domain.agents.apps.conftest import ToolCapableFakeLLM


def test_create_analyst_app_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_analyst_app()
    assert callable(getattr(app, "invoke", None))


def test_summary_schema_has_title_field() -> None:
    fields = mod.SummarySchema.model_fields
    assert "title" in fields


def test_summary_schema_has_key_points_field() -> None:
    fields = mod.SummarySchema.model_fields
    assert "key_points" in fields


def test_summary_schema_has_sentiment_field() -> None:
    fields = mod.SummarySchema.model_fields
    assert "sentiment" in fields
