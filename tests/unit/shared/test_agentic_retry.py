"""Unit tests for src.shared.agentic.retry."""

from __future__ import annotations

import random

import pytest

from src.shared.agentic.retry import (
    AgentTerminalError,
    AgentTransientStallError,
    MIN_DELAY_MS,
    RetryConfig,
    classify_failure,
    compute_delay,
)


class TestClassifyFailure:
    def test_transient_stall_returns_continuation(self) -> None:
        assert classify_failure(AgentTransientStallError("stalled")) == "continuation"

    def test_terminal_returns_none(self) -> None:
        assert classify_failure(AgentTerminalError("config bad")) is None

    def test_generic_exception_returns_failure(self) -> None:
        assert classify_failure(RuntimeError("boom")) == "failure"

    def test_base_exception_non_exception_returns_none(self) -> None:
        # KeyboardInterrupt etc. are BaseException but not Exception → no retry.
        assert classify_failure(KeyboardInterrupt()) is None


class TestComputeDelay:
    def test_continuation_at_attempt_two_returns_fixed_delay(self) -> None:
        cfg = RetryConfig(continuation_delay_ms=4321)
        assert compute_delay(attempt=2, kind="continuation", config=cfg) == 4321

    def test_failure_uses_exponential_backoff(self) -> None:
        cfg = RetryConfig(failure_base_ms=10_000, jitter_ratio=0.0)
        # attempt=1 → 10_000 * 2^0 = 10_000
        # attempt=3 → 10_000 * 2^2 = 40_000
        assert compute_delay(attempt=1, kind="failure", config=cfg) == 10_000
        assert compute_delay(attempt=3, kind="failure", config=cfg) == 40_000

    def test_failure_capped_at_max_backoff(self) -> None:
        cfg = RetryConfig(
            failure_base_ms=10_000, max_backoff_ms=20_000, jitter_ratio=0.0
        )
        assert compute_delay(attempt=10, kind="failure", config=cfg) == 20_000

    def test_min_floor_applied(self) -> None:
        cfg = RetryConfig(failure_base_ms=100, jitter_ratio=0.0)
        assert compute_delay(attempt=1, kind="failure", config=cfg) == MIN_DELAY_MS

    def test_jitter_uses_injected_rng(self) -> None:
        cfg = RetryConfig(failure_base_ms=10_000, jitter_ratio=0.5)
        rng = random.Random(0)
        delay = compute_delay(attempt=1, kind="failure", config=cfg, rng=rng)
        assert isinstance(delay, int)
        assert delay >= MIN_DELAY_MS

    def test_attempt_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_delay(attempt=0, kind="failure", config=RetryConfig())
