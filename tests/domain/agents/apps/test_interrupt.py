"""Tests for the interrupt (HITL) app."""

from unittest.mock import patch

import src.domain.agents.apps.interrupt as mod
from tests.domain.agents.apps.conftest import ToolCapableFakeLLM


def test_create_interrupt_app_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_interrupt_app()
    assert callable(getattr(app, "invoke", None))


def test_list_records_tool_exists() -> None:
    assert mod.list_records is not None
    assert hasattr(mod.list_records, "invoke")


def test_delete_record_tool_exists() -> None:
    assert mod.delete_record is not None
    assert hasattr(mod.delete_record, "invoke")
