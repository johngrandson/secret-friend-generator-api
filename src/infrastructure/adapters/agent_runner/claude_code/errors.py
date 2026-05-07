"""Exception hierarchy for the Claude Code runner.

Each error subclasses ``AgentRunnerError`` so use cases can catch all runner
failures with a single narrow clause. Adapters that need to translate these
into the shared agentic retry markers (``AgentTransientStallError`` /
``AgentTerminalError``) do so at the orchestration layer, not here — keeps
this module decoupled from deeper ``shared.agentic`` imports beyond the base.
"""

from src.shared.agentic.agent_runner import AgentRunnerError


class ClaudeCodeRunnerError(AgentRunnerError):
    """Base error for any failure in the Claude Code runner."""


class ClaudeCodeBinaryNotFoundError(ClaudeCodeRunnerError):
    """The configured ``command`` is not on PATH."""


class ClaudeCodeTimeoutError(ClaudeCodeRunnerError):
    """A timeout fired (turn deadline or stall window)."""

    def __init__(self, message: str, *, kind: str) -> None:
        super().__init__(message)
        self.kind = kind  # "turn" or "stall"


class ClaudeCodeExitError(ClaudeCodeRunnerError):
    """The CLI exited with a non-zero status."""

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class ClaudeCodeResultError(ClaudeCodeRunnerError):
    """The CLI emitted a ``result`` event with ``is_error: true``."""


class ClaudeCodeInputRequiredError(ClaudeCodeRunnerError):
    """The agent asked for user input — fails in unattended mode."""


class ClaudeCodePromptTooLargeError(ClaudeCodeRunnerError):
    """The prompt exceeds the runner's hard byte cap."""
