"""IAgentRunner Protocol + value types — kernel agent invocation contract.

Concrete implementations (``ClaudeCodeRunner``, future ``OpenAIRunner``,
etc.) live in ``src/infrastructure/adapters/`` and satisfy this Protocol
structurally — no inheritance required.

``TurnResult`` and ``TokenUsage`` are frozen dataclasses so the kernel
stays Pydantic-free; adapters that prefer Pydantic for their internal
parsing translate to these types at the boundary.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

AgentEventCallback = Callable[[dict[str, Any]], Awaitable[None] | None]


class AgentRunnerError(Exception):
    """Base error raised by IAgentRunner implementations.

    Adapters subclass this so callers can catch all runner failures narrowly
    without resorting to a bare ``except Exception``.
    """


@dataclass(frozen=True)
class TokenUsage:
    """Token counts for a single turn. Defaults to zero if no usage emitted."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")


@dataclass(frozen=True)
class TurnResult:
    """Outcome of a single agent-runner turn."""

    session_id: str | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    text: str = ""
    is_error: bool = False
    error_message: str | None = None


@runtime_checkable
class IAgentRunner(Protocol):
    """Run one conversational turn against an agent backend."""

    async def run_turn(
        self,
        *,
        prompt: str,
        workspace: Path,
        session_id: str | None = None,
        on_event: AgentEventCallback | None = None,
    ) -> TurnResult: ...
