"""Unit tests for src.shared.agentic.agent_runner value objects."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.shared.agentic.agent_runner import IAgentRunner, TokenUsage, TurnResult


class TestTokenUsage:
    def test_defaults_to_zero(self) -> None:
        u = TokenUsage()
        assert (u.input_tokens, u.output_tokens, u.total_tokens) == (0, 0, 0)

    def test_is_frozen(self) -> None:
        u = TokenUsage(input_tokens=1)
        with pytest.raises(FrozenInstanceError):
            u.input_tokens = 9  # type: ignore[misc]

    @pytest.mark.parametrize(
        "field",
        ["input_tokens", "output_tokens", "total_tokens"],
    )
    def test_negative_values_raise(self, field: str) -> None:
        with pytest.raises(ValueError):
            TokenUsage(**{field: -1})  # type: ignore[arg-type]


class TestTurnResult:
    def test_default_usage_is_zero_tokenusage(self) -> None:
        result = TurnResult()
        assert isinstance(result.usage, TokenUsage)
        assert result.session_id is None
        assert result.is_error is False

    def test_is_frozen(self) -> None:
        result = TurnResult(text="hello")
        with pytest.raises(FrozenInstanceError):
            result.text = "bye"  # type: ignore[misc]


class TestIAgentRunnerProtocol:
    def test_runtime_checkable_satisfied_by_duck_type(self) -> None:
        class _DuckRunner:
            async def run_turn(
                self, *, prompt: str, workspace, session_id=None
            ) -> TurnResult:  # noqa: ANN001
                return TurnResult(text=prompt)

        assert isinstance(_DuckRunner(), IAgentRunner)
