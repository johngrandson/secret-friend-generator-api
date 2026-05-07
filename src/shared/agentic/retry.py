"""Retry decision logic — pure functions, no I/O.

Two helpers callable from any agentic vertical's orchestrator:

- ``classify_failure(err)`` — labels an exception:
    - ``"continuation"`` (transient stall, fast retry)
    - ``"failure"`` (other retryable error, exponential backoff)
    - ``None`` (non-retryable, mark failed and stop)

- ``compute_delay(attempt, kind, config)`` — milliseconds before the next
  attempt:

      continuation + attempt 2  -> RetryConfig.continuation_delay_ms
      failure (or attempt > 2)  -> failure_base_ms * 2^(attempt-1)
                                   capped at max_backoff_ms,
                                   ± jitter_ratio of the base,
                                   floored at MIN_DELAY_MS.

Adapters wrap their concrete errors as ``AgentTransientStallError`` (stall
condition the agent can recover from) or ``AgentTerminalError`` (operator
must intervene). All other ``Exception`` subclasses default to retryable
``"failure"`` so a network blip or DB hiccup gets at least one retry.
"""

import random
from dataclasses import dataclass
from typing import Final, Literal

from src.shared.agentic.agent_runner import AgentRunnerError

RetryKind = Literal["continuation", "failure"]

MIN_DELAY_MS: Final[int] = 1_000
MAX_DOUBLING_EXPONENT: Final[int] = 10


class AgentTransientStallError(AgentRunnerError):
    """Marker: agent stalled and a fast retry is appropriate (no backoff)."""


class AgentTerminalError(AgentRunnerError):
    """Marker: operator must intervene; retrying just burns budget."""


@dataclass(frozen=True)
class RetryConfig:
    """Tunable retry policy. Defaults match the Symphony origin behaviour."""

    continuation_delay_ms: int = 5_000
    failure_base_ms: int = 30_000
    max_backoff_ms: int = 30 * 60 * 1_000
    jitter_ratio: float = 0.2


def classify_failure(err: BaseException) -> RetryKind | None:
    """Decide whether ``err`` should trigger a retry."""
    if isinstance(err, AgentTransientStallError):
        return "continuation"
    if isinstance(err, AgentTerminalError):
        return None
    if isinstance(err, Exception):
        return "failure"
    return None


def compute_delay(
    *,
    attempt: int,
    kind: RetryKind,
    config: RetryConfig,
    rng: random.Random | None = None,
) -> int:
    """Milliseconds to sleep before retry ``attempt``.

    ``attempt`` is the NEXT attempt's number (the delay before the second
    try uses ``attempt=2``). Tests inject ``rng`` for deterministic jitter.
    """
    if attempt < 1:
        raise ValueError(f"attempt must be >= 1; got {attempt}")

    if kind == "continuation" and attempt == 2:
        return config.continuation_delay_ms

    exponent = min(attempt - 1, MAX_DOUBLING_EXPONENT)
    base = min(config.failure_base_ms * (1 << exponent), config.max_backoff_ms)
    jitter_source = rng if rng is not None else random
    jitter = int(base * config.jitter_ratio * (jitter_source.random() * 2 - 1))
    return max(MIN_DELAY_MS, base + jitter)
