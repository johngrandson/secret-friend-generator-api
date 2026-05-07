"""Default values + regex patterns for the workflow loader and schemas.

Splits the magic numbers previously inlined in ``schemas.py`` (polling,
agent timeouts, claude turn/stall, retry deltas) and the env-var regex
from ``loader.py`` into a single import target.
"""

import re
from typing import Final

DEFAULT_POLLING_INTERVAL_MS: Final[int] = 30_000
"""How often the orchestrator polls the tracker (default: 30s)."""

DEFAULT_AGENT_TIMEOUT_MS: Final[int] = 1_800_000
"""Agent process wall clock (default: 30min)."""

DEFAULT_TURN_TIMEOUT_MS: Final[int] = 600_000
"""Single ``claude`` turn wall clock (default: 10min)."""

DEFAULT_STALL_TIMEOUT_MS: Final[int] = 120_000
"""No-event detection window inside a turn (default: 2min)."""

DEFAULT_RETRY_CONTINUATION_MS: Final[int] = 1_000
"""Pause before the second attempt after a continuation (workflow schema default)."""

DEFAULT_RETRY_FAILURE_BASE_MS: Final[int] = 10_000
"""Base for exponential failure backoff (workflow schema default)."""

DEFAULT_RETRY_MAX_BACKOFF_MS: Final[int] = 600_000
"""Cap on exponential backoff (workflow schema default: 10min)."""

DEFAULT_RETRY_MAX_ATTEMPTS: Final[int] = 3
"""Inclusive total attempts allowed (workflow schema default)."""

DEFAULT_RETRY_JITTER_RATIO: Final[float] = 0.05
"""Jitter applied to backoff (workflow schema default)."""

ENV_VAR_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\$([A-Z_][A-Z0-9_]*)$")
"""Match ``$VAR_NAME`` references for env-var resolution."""

FRONT_MATTER_DELIMITER: Final[str] = "---"
"""Opening / closing line for YAML front matter blocks."""
