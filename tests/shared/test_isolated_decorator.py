"""Tests for the @isolated decorator in src/shared/signals.py."""

import logging

import pytest

from src.shared.signals import isolated


def test_isolated_returns_function_result_on_success() -> None:
    @isolated
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5


def test_isolated_swallows_exception_and_returns_none() -> None:
    @isolated
    def explode() -> None:
        raise ValueError("boom")

    result = explode()
    assert result is None


def test_isolated_logs_exception(caplog: pytest.LogCaptureFixture) -> None:
    @isolated
    def boom() -> None:
        raise RuntimeError("test error")

    with caplog.at_level(logging.ERROR, logger="src.shared.signals"):
        boom()

    assert any("lifecycle handler failed" in r.message for r in caplog.records)


def test_isolated_preserves_function_name() -> None:
    @isolated
    def my_named_handler() -> None:
        pass

    assert my_named_handler.__name__ == "my_named_handler"
