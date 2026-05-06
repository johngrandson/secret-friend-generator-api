"""Unit tests for src.shared.agentic.workspace VOs."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.shared.agentic.workspace import HookResult, Workspace


class TestWorkspace:
    def test_is_frozen(self) -> None:
        ws = Workspace(path=Path("/tmp/ws"), key="abc", created_now=True)
        with pytest.raises(FrozenInstanceError):
            ws.created_now = False  # type: ignore[misc]

    def test_empty_key_raises(self) -> None:
        with pytest.raises(ValueError):
            Workspace(path=Path("/tmp/ws"), key="", created_now=True)


class TestHookResult:
    def test_is_frozen(self) -> None:
        hr = HookResult(name="after_create", exit_code=0, output="ok")
        with pytest.raises(FrozenInstanceError):
            hr.exit_code = 1  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            HookResult(name="", exit_code=0, output="")

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(ValueError):
            HookResult(name="x", exit_code=0, output="", duration_ms=-1)
