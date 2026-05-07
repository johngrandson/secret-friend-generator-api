"""Tunables for the Claude Code agent-runner adapter.

Single import target for byte caps and subprocess timeouts the runner
and arg-builder used to inline.
"""

from typing import Final

MAX_PROMPT_BYTES: Final[int] = 100_000
"""Reject prompts above this size before they reach the CLI."""

KILL_TIMEOUT_SECONDS: Final[int] = 5
"""How long to wait after ``proc.kill()`` before giving up on the wait."""
