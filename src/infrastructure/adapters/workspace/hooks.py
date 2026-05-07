"""Hook subprocess executor.

Runs an operator-supplied bash script (``hooks.after_create``,
``hooks.before_run``, etc.) in the workspace directory, captures merged
stdout+stderr, and enforces a timeout. Thin wrapper around
``asyncio.create_subprocess_exec``; the upper layer decides what to do
with the returned ``HookResult`` based on the hook's failure policy.
"""

import asyncio
import logging
import time
from pathlib import Path

from src.infrastructure.adapters.workspace.constants import (
    DEFAULT_HOOK_TIMEOUT_SECONDS,
    MAX_HOOK_OUTPUT_BYTES,
)
from src.shared.agentic.workspace import HookResult

log = logging.getLogger(__name__)


class HookError(Exception):
    """Base error for hook execution failures."""


class HookTimeoutError(HookError):
    """The hook script ran longer than its configured timeout."""

    def __init__(self, message: str, *, name: str, timeout_seconds: float) -> None:
        super().__init__(message)
        self.name = name
        self.timeout_seconds = timeout_seconds


async def exec_hook(
    *,
    name: str,
    script: str,
    cwd: Path,
    timeout_seconds: float = DEFAULT_HOOK_TIMEOUT_SECONDS,
) -> HookResult:
    """Spawn ``bash -c <script>`` in ``cwd``, return a ``HookResult``.

    Raises:
        HookTimeoutError: the script ran longer than ``timeout_seconds``.
            The subprocess is killed before returning.
    """
    started = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        "bash",
        "-c",
        script,
        cwd=str(cwd),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout_bytes, _ = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except TimeoutError as err:
        proc.kill()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except TimeoutError:
            log.warning("Hook %r did not exit after kill", name)
        raise HookTimeoutError(
            f"Hook {name!r} exceeded {timeout_seconds}s timeout",
            name=name,
            timeout_seconds=timeout_seconds,
        ) from err

    duration_ms = int((time.monotonic() - started) * 1000)
    capped = stdout_bytes[:MAX_HOOK_OUTPUT_BYTES]
    output = capped.decode("utf-8", errors="replace")
    exit_code = proc.returncode if proc.returncode is not None else -1
    return HookResult(
        name=name, exit_code=exit_code, output=output, duration_ms=duration_ms
    )
