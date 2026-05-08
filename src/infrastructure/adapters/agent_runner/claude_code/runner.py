"""Claude Code CLI runner — implements ``IAgentRunner`` via subprocess.

One ``run_turn`` call = one ``claude`` process. Session continuity across
turns: the ``session_id`` from ``TurnResult`` becomes ``--resume <id>`` on
the next call. Tests inject ``process_factory`` to skip the subprocess.

The Protocol ``IAgentRunner.run_turn`` exposes only the per-turn inputs
(prompt / workspace / session_id). CLI config and the optional event hook
are wired at construction time so this class satisfies the kernel Protocol
without leaking adapter-specific arguments.
"""

import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

from src.infrastructure.adapters.agent_runner.claude_code.args import (
    build_args,
    validate_prompt,
)
from src.infrastructure.adapters.agent_runner.claude_code.errors import (
    ClaudeCodeExitError,
    ClaudeCodeInputRequiredError,
    ClaudeCodeResultError,
    ClaudeCodeTimeoutError,
)
from src.infrastructure.adapters.agent_runner.claude_code.parser import (
    TurnState,
    read_stream,
)
from src.shared.agentic.agent_runner import AgentEventCallback
from src.infrastructure.adapters.agent_runner.claude_code.transport import (
    ProcessFactory,
    default_process_factory,
)
from src.infrastructure.adapters.agent_runner.constants import KILL_TIMEOUT_SECONDS
from src.infrastructure.adapters.workflow import ClaudeCodeConfig
from src.shared.agentic.agent_runner import TurnResult

log = logging.getLogger(__name__)


class ClaudeCodeRunner:
    """Implements ``IAgentRunner`` by shelling out to the ``claude`` CLI."""

    def __init__(
        self,
        *,
        config: ClaudeCodeConfig,
        process_factory: ProcessFactory | None = None,
        on_event: AgentEventCallback | None = None,
    ) -> None:
        self._config = config
        self._factory = process_factory or default_process_factory
        self._on_event = on_event

    async def run_turn(
        self,
        *,
        prompt: str,
        workspace: Path,
        session_id: str | None = None,
        on_event: AgentEventCallback | None = None,
    ) -> TurnResult:
        """Run one ``claude`` CLI turn and return the aggregated result.

        Raises:
            ClaudeCodePromptTooLargeError: prompt exceeds MAX_PROMPT_BYTES.
            ClaudeCodeBinaryNotFoundError: ``config.command`` not on PATH.
            ClaudeCodeTimeoutError: stall or turn deadline fired.
            ClaudeCodeExitError: process exited non-zero.
            ClaudeCodeResultError: result event reported is_error=true.
            ClaudeCodeInputRequiredError: agent requested user input.
        """
        validate_prompt(prompt)
        args = build_args(prompt=prompt, config=self._config, session_id=session_id)
        effective_on_event = on_event or self._on_event
        turn_seconds = self._config.turn_timeout_ms / 1000.0
        try:
            return await asyncio.wait_for(
                self._run_turn_inner(args, workspace, effective_on_event),
                timeout=turn_seconds,
            )
        except TimeoutError as err:
            raise ClaudeCodeTimeoutError(
                f"Turn timeout after {self._config.turn_timeout_ms}ms",
                kind="turn",
            ) from err

    async def _run_turn_inner(
        self,
        args: Sequence[str],
        cwd: Path,
        on_event: AgentEventCallback | None = None,
    ) -> TurnResult:
        proc = await self._factory(args, cwd)
        state = TurnState()
        try:
            await read_stream(
                proc, state, self._config.stall_timeout_ms, on_event
            )
            exit_code = await proc.wait()
        finally:
            if proc.returncode is None:
                proc.kill()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=KILL_TIMEOUT_SECONDS)
                except TimeoutError:
                    log.warning("Claude process did not exit after kill")

        if (
            state.is_error
            and state.error_message
            and "user input" in state.error_message
        ):
            raise ClaudeCodeInputRequiredError(state.error_message)
        if exit_code != 0:
            raise ClaudeCodeExitError(
                f"Claude CLI exited with status {exit_code}", exit_code=exit_code
            )
        if state.is_error:
            raise ClaudeCodeResultError(state.error_message or "unknown result error")

        return TurnResult(
            session_id=state.session_id,
            usage=state.usage,
            text="".join(state.text_parts),
            is_error=False,
            error_message=None,
        )
