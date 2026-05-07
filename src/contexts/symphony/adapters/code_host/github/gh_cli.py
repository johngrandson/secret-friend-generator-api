"""Subprocess transport for the GitHub ``gh`` CLI adapter.

Defines ``SubprocessRunner`` (Protocol-shaped Callable type) and the
production runner that spawns processes via
``asyncio.create_subprocess_exec``. Tests inject scripted runners — the
adapter has no hard dependency on real subprocess behaviour.

``bash -c`` is deliberately NOT used: the PR body contains backticks /
dollar signs that would need shell escaping. Bodies are delivered to
``gh pr create -F -`` / ``gh pr edit -F -`` via stdin instead.
"""

import asyncio
import shutil
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from src.contexts.symphony.domain.code_host import (
    CodeHostBinaryNotFoundError,
    CodeHostError,
)


@dataclass(frozen=True)
class SubprocessResult:
    """Captured outcome of one subprocess invocation."""

    exit_code: int
    stdout: bytes
    stderr: bytes


SubprocessRunner = Callable[
    [Sequence[str], Path, bytes | None], Awaitable[SubprocessResult]
]


async def default_subprocess_runner(
    argv: Sequence[str], cwd: Path, stdin: bytes | None
) -> SubprocessResult:
    """Production runner: spawn ``argv[0]`` via ``asyncio.create_subprocess_exec``.

    Raises:
        CodeHostError: empty argv.
        CodeHostBinaryNotFoundError: ``argv[0]`` is not on PATH.
    """
    if not argv:
        raise CodeHostError("Empty argv")
    exe = shutil.which(argv[0])
    if exe is None:
        raise CodeHostBinaryNotFoundError(f"Binary not found on PATH: {argv[0]!r}")
    stdin_target = (
        asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL
    )
    proc = await asyncio.create_subprocess_exec(
        exe,
        *argv[1:],
        cwd=str(cwd),
        stdin=stdin_target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=stdin)
    return SubprocessResult(
        exit_code=proc.returncode if proc.returncode is not None else -1,
        stdout=stdout,
        stderr=stderr,
    )
