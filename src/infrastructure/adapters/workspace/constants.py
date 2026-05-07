"""Tunables and regex patterns for the filesystem workspace manager.

Single import target for hook timeouts, output caps, key sanitization
patterns and the hook-name → abort-policy mapping previously inlined in
``filesystem.py`` and ``hooks.py``.
"""

import re
from typing import Final

DEFAULT_HOOK_TIMEOUT_SECONDS: Final[float] = 600.0
"""Per-hook wall-clock cap (default: 10min)."""

MAX_HOOK_OUTPUT_BYTES: Final[int] = 1_000_000
"""1MB cap on captured stdout+stderr per hook run."""

UNSAFE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9._-]")
"""Characters replaced with ``_`` when sanitizing workspace keys."""

MAX_KEY_LENGTH: Final[int] = 64
"""Truncation length for sanitized workspace keys."""

FALLBACK_KEY: Final[str] = "_"
"""Returned when the sanitized identifier is empty."""

ABORT_ON_FAILURE_HOOKS: Final[frozenset[str]] = frozenset(
    {"after_create", "before_run"}
)
"""Hooks whose non-zero exit must abort the surrounding operation."""
