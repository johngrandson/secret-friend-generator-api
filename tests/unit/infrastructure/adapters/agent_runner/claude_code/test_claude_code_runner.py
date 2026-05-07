"""Unit tests for ClaudeCodeRunner with a fake ProcessFactory.

Avoids spawning ``claude`` — scripted stdout drives the parser end-to-end.
"""

import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from src.infrastructure.adapters.agent_runner.claude_code import (
    ClaudeCodeExitError,
    ClaudeCodeInputRequiredError,
    ClaudeCodePromptTooLargeError,
    ClaudeCodeResultError,
    ClaudeCodeRunner,
    ClaudeCodeTimeoutError,
    build_args,
    validate_prompt,
)
from src.infrastructure.adapters.agent_runner.claude_code.transport import (
    ProcessProtocol,
    StreamProtocol,
)
from src.infrastructure.adapters.workflow import ClaudeCodeConfig


class _FakeStream:
    """async readline()-conformant queue of pre-baked bytes lines."""

    def __init__(self, lines: list[bytes]) -> None:
        self._lines = list(lines)

    async def readline(self) -> bytes:
        if not self._lines:
            return b""
        return self._lines.pop(0)


class _FakeProcess:
    def __init__(
        self,
        *,
        lines: list[bytes],
        exit_code: int = 0,
        wait_delay: float = 0.0,
    ) -> None:
        self._stdout: StreamProtocol = _FakeStream(lines)
        self._exit_code = exit_code
        self._wait_delay = wait_delay
        self._returncode: int | None = None
        self.killed = False

    @property
    def stdout(self) -> StreamProtocol | None:
        return self._stdout

    @property
    def returncode(self) -> int | None:
        return self._returncode

    async def wait(self) -> int:
        if self._wait_delay:
            await asyncio.sleep(self._wait_delay)
        self._returncode = self._exit_code
        return self._exit_code

    def kill(self) -> None:
        self.killed = True
        self._returncode = -9


def _factory_from(proc: _FakeProcess) -> Any:
    async def factory(args: Sequence[str], cwd: Path) -> ProcessProtocol:
        return proc

    return factory


def _config(**overrides: Any) -> ClaudeCodeConfig:
    return ClaudeCodeConfig(**overrides)


def _result_line(**fields: Any) -> bytes:
    payload = {"type": "result", **fields}
    return (json.dumps(payload) + "\n").encode("utf-8")


def _assistant_line(text: str) -> bytes:
    payload = {
        "type": "assistant",
        "message": {
            "content": [{"type": "text", "text": text}],
        },
    }
    return (json.dumps(payload) + "\n").encode("utf-8")


@pytest.mark.asyncio
async def test_run_turn_aggregates_session_text_and_usage(tmp_path: Path) -> None:
    lines = [
        _assistant_line("hello "),
        _assistant_line("world"),
        _result_line(
            session_id="sess-1",
            usage={
                "input_tokens": 10,
                "output_tokens": 5,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        ),
    ]
    proc = _FakeProcess(lines=lines, exit_code=0)
    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=0), process_factory=_factory_from(proc)
    )

    result = await runner.run_turn(prompt="hi", workspace=tmp_path)

    assert result.session_id == "sess-1"
    assert result.text == "hello world"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 5
    assert result.usage.total_tokens == 15
    assert result.is_error is False


@pytest.mark.asyncio
async def test_run_turn_skips_non_json_and_non_dict_lines(tmp_path: Path) -> None:
    lines = [
        b"not a json line\n",
        b"42\n",  # JSON but not a dict
        _assistant_line("ok"),
        _result_line(session_id="s"),
    ]
    proc = _FakeProcess(lines=lines, exit_code=0)
    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=0), process_factory=_factory_from(proc)
    )
    result = await runner.run_turn(prompt="hi", workspace=tmp_path)
    assert result.text == "ok"


@pytest.mark.asyncio
async def test_run_turn_raises_on_nonzero_exit(tmp_path: Path) -> None:
    proc = _FakeProcess(lines=[_result_line(session_id="s")], exit_code=2)
    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=0), process_factory=_factory_from(proc)
    )
    with pytest.raises(ClaudeCodeExitError) as exc:
        await runner.run_turn(prompt="hi", workspace=tmp_path)
    assert exc.value.exit_code == 2


@pytest.mark.asyncio
async def test_run_turn_raises_on_result_event_error(tmp_path: Path) -> None:
    lines = [_result_line(is_error=True, error="boom", session_id="s")]
    proc = _FakeProcess(lines=lines, exit_code=0)
    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=0), process_factory=_factory_from(proc)
    )
    with pytest.raises(ClaudeCodeResultError, match="boom"):
        await runner.run_turn(prompt="hi", workspace=tmp_path)


@pytest.mark.asyncio
async def test_run_turn_raises_input_required_on_input_request(
    tmp_path: Path,
) -> None:
    lines = [
        (json.dumps({"type": "input_request"}) + "\n").encode("utf-8"),
        _result_line(session_id="s"),
    ]
    proc = _FakeProcess(lines=lines, exit_code=0)
    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=0), process_factory=_factory_from(proc)
    )
    with pytest.raises(ClaudeCodeInputRequiredError):
        await runner.run_turn(prompt="hi", workspace=tmp_path)


@pytest.mark.asyncio
async def test_run_turn_stall_timeout_when_no_lines(tmp_path: Path) -> None:
    """No lines + stall_timeout_ms>0 fires stall before EOF if readline blocks."""

    class _BlockingStream:
        async def readline(self) -> bytes:
            await asyncio.sleep(10)
            return b""

    class _BlockingProc:
        def __init__(self) -> None:
            self._stdout: StreamProtocol = _BlockingStream()
            self.returncode_value: int | None = None
            self.killed = False

        @property
        def stdout(self) -> StreamProtocol | None:
            return self._stdout

        @property
        def returncode(self) -> int | None:
            return self.returncode_value

        async def wait(self) -> int:
            return 0

        def kill(self) -> None:
            self.killed = True
            self.returncode_value = -9

    proc = _BlockingProc()

    async def factory(args: Sequence[str], cwd: Path) -> ProcessProtocol:
        return proc

    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=20, turn_timeout_ms=5_000),
        process_factory=factory,
    )
    with pytest.raises(ClaudeCodeTimeoutError) as exc:
        await runner.run_turn(prompt="hi", workspace=tmp_path)
    assert exc.value.kind == "stall"


@pytest.mark.asyncio
async def test_run_turn_turn_timeout(tmp_path: Path) -> None:
    """turn_timeout_ms wraps the whole inner run."""

    class _NeverEndingStream:
        async def readline(self) -> bytes:
            await asyncio.sleep(10)
            return b""

    class _SlowProc:
        def __init__(self) -> None:
            self._stdout: StreamProtocol = _NeverEndingStream()
            self.returncode_value: int | None = None

        @property
        def stdout(self) -> StreamProtocol | None:
            return self._stdout

        @property
        def returncode(self) -> int | None:
            return self.returncode_value

        async def wait(self) -> int:
            return 0

        def kill(self) -> None:
            self.returncode_value = -9

    proc = _SlowProc()

    async def factory(args: Sequence[str], cwd: Path) -> ProcessProtocol:
        return proc

    runner = ClaudeCodeRunner(
        config=_config(stall_timeout_ms=0, turn_timeout_ms=1_000),
        process_factory=factory,
    )
    with pytest.raises(ClaudeCodeTimeoutError) as exc:
        await runner.run_turn(prompt="hi", workspace=tmp_path)
    assert exc.value.kind == "turn"


def test_validate_prompt_rejects_oversized() -> None:
    big = "a" * 200_000
    with pytest.raises(ClaudeCodePromptTooLargeError):
        validate_prompt(big)


def test_build_args_assembles_expected_flags() -> None:
    cfg = _config(api_model="model-x", mcp_config_path=".mcp.json")
    args = build_args(prompt="hi", config=cfg, session_id="sess-1")
    assert args[0] == "claude"
    assert "--print" in args
    assert "stream-json" in args
    assert "--allowedTools" in args
    assert "--model" in args and "model-x" in args
    assert "--mcp-config" in args and ".mcp.json" in args
    assert "--resume" in args and "sess-1" in args
    assert args[-2:] == ["-p", "hi"]


def test_build_args_omits_optional_flags_when_unset() -> None:
    cfg = _config()
    args = build_args(prompt="hi", config=cfg, session_id=None)
    assert "--resume" not in args
    assert "--mcp-config" not in args
