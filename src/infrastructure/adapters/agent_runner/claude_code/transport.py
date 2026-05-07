"""Subprocess transport — Protocol types + the production process factory."""

import asyncio
import shutil
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Protocol

from src.infrastructure.adapters.agent_runner.claude_code.errors import (
    ClaudeCodeBinaryNotFoundError,
    ClaudeCodeRunnerError,
)


class StreamProtocol(Protocol):
    async def readline(self) -> bytes: ...


class ProcessProtocol(Protocol):
    @property
    def stdout(self) -> StreamProtocol | None: ...

    @property
    def returncode(self) -> int | None: ...

    async def wait(self) -> int: ...

    def kill(self) -> None: ...


ProcessFactory = Callable[[Sequence[str], Path], Awaitable[ProcessProtocol]]


async def default_process_factory(
    args: Sequence[str], cwd: Path
) -> ProcessProtocol:
    """Spawn ``claude`` via ``asyncio.create_subprocess_exec``.

    Raises:
        ClaudeCodeRunnerError: empty argv.
        ClaudeCodeBinaryNotFoundError: ``args[0]`` is not on PATH.
    """
    if not args:
        raise ClaudeCodeRunnerError("Empty argv")
    exe_path = shutil.which(args[0])
    if exe_path is None:
        raise ClaudeCodeBinaryNotFoundError(
            f"Claude Code CLI not found on PATH: {args[0]!r}"
        )
    proc = await asyncio.create_subprocess_exec(
        exe_path,
        *args[1:],
        cwd=str(cwd),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    return proc
