"""stream-json parser — reads ``claude`` events, aggregates into ``TurnState``.

The parser stays defensive: any partial / non-JSON / non-dict line is logged
and skipped so a single malformed event never aborts the turn.
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from src.infrastructure.adapters.agent_runner.claude_code.errors import (
    ClaudeCodeRunnerError,
    ClaudeCodeTimeoutError,
)
from src.infrastructure.adapters.agent_runner.claude_code.transport import (
    ProcessProtocol,
)
from src.shared.agentic.agent_runner import TokenUsage

log = logging.getLogger(__name__)

# Stream-json event shape — opaque dict from the Claude CLI. Handlers must
# narrow with isinstance / .get() before accessing fields. Using `object` over
# `Any` keeps the type honest and prevents accidental attribute access.
EventCallback = Callable[[dict[str, object]], Awaitable[None] | None]


@dataclass
class TurnState:
    """Mutable accumulator folded by the stream-json parser into a TurnResult."""

    session_id: str | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    text_parts: list[str] = field(default_factory=list)
    is_error: bool = False
    error_message: str | None = None


async def read_stream(
    proc: ProcessProtocol,
    state: TurnState,
    stall_timeout_ms: int,
    on_event: EventCallback | None,
) -> None:
    """Drain stdout, parse each line as stream-json, fold into ``state``.

    Raises:
        ClaudeCodeRunnerError: process has no stdout pipe.
        ClaudeCodeTimeoutError(kind="stall"): no line arrived within
            ``stall_timeout_ms``. Returns normally on EOF.
    """
    if proc.stdout is None:
        raise ClaudeCodeRunnerError("Process has no stdout pipe")

    stall_seconds: float | None = (
        stall_timeout_ms / 1000.0 if stall_timeout_ms > 0 else None
    )

    while True:
        try:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=stall_seconds)
        except TimeoutError as err:
            raise ClaudeCodeTimeoutError(
                f"Stall timeout after {stall_timeout_ms}ms of no output",
                kind="stall",
            ) from err

        if not line:
            return  # EOF — process is finishing

        text_line = line.decode("utf-8", errors="replace").rstrip("\r\n")
        if not text_line:
            continue

        try:
            event = json.loads(text_line)
        except json.JSONDecodeError:
            log.debug("Claude non-JSON stream line: %s", text_line[:200])
            continue

        if not isinstance(event, dict):
            continue

        _handle_event(event, state)
        if on_event is not None:
            result = on_event(event)
            if asyncio.iscoroutine(result):
                await result


def _handle_event(event: dict[str, object], state: TurnState) -> None:
    event_type = event.get("type")

    if event_type == "result":
        _handle_result_event(event, state)
    elif event_type == "input_request":
        state.is_error = True
        state.error_message = (
            "Claude requested user input (unsupported in unattended mode)"
        )
    elif event_type == "assistant":
        _handle_assistant_event(event, state)
    elif event_type == "system" and event.get("subtype") == "error":
        log.warning("Claude system error: %s", event)
    # Unknown / informational events pass through to ``on_event`` only.


def _handle_result_event(event: dict[str, object], state: TurnState) -> None:
    session_id = event.get("session_id")
    if isinstance(session_id, str):
        state.session_id = session_id

    if event.get("is_error") or event.get("subtype") == "error_result":
        state.is_error = True
        error = event.get("error") or event.get("message") or "unknown error"
        state.error_message = error if isinstance(error, str) else "unknown error"

    usage = event.get("usage")
    if isinstance(usage, dict):
        state.usage = _coerce_usage(usage)


def _handle_assistant_event(event: dict[str, object], state: TurnState) -> None:
    message = event.get("message")
    if not isinstance(message, dict):
        return

    content = message.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    state.text_parts.append(text)

    usage = message.get("usage")
    if isinstance(usage, dict):
        state.usage = _coerce_usage(usage, fallback=state.usage)


def _coerce_usage(
    usage: dict[str, object], fallback: TokenUsage | None = None
) -> TokenUsage:
    base = fallback or TokenUsage()
    input_tokens = _int_or(usage.get("input_tokens"), base.input_tokens)
    output_tokens = _int_or(usage.get("output_tokens"), base.output_tokens)
    # Real CLI omits ``total_tokens`` and instead reports the cache split.
    # Treat all four as billed input and derive the total when missing.
    cache_creation = _int_or(usage.get("cache_creation_input_tokens"), 0)
    cache_read = _int_or(usage.get("cache_read_input_tokens"), 0)
    # Anthropic stream-json convention: input_tokens excludes cache (cache_creation
    # and cache_read are reported separately), so summing all four gives true total.
    derived_total = input_tokens + output_tokens + cache_creation + cache_read
    total_tokens = _int_or(usage.get("total_tokens"), derived_total)
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def _int_or(value: object, fallback: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return fallback
