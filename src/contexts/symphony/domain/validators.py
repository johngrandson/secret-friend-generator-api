"""Pure-Python validators reused across symphony domain entities.

These helpers replace the ``if not X.strip(): raise ValueError(...)`` snippet
duplicated 17 times across entity factories and mutation methods. Functions
raise ``ValueError`` so existing call sites and tests continue to assert the
same exception type.
"""

from src.contexts.symphony.domain.constants import MIN_ARTIFACT_VERSION


def ensure_non_blank(value: str, field_name: str) -> None:
    """Raise ``ValueError`` if ``value`` is empty or whitespace-only."""
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank.")


def ensure_min_version(version: int, *, minimum: int = MIN_ARTIFACT_VERSION) -> None:
    """Raise ``ValueError`` if ``version`` is below ``minimum`` (default 1)."""
    if version < minimum:
        raise ValueError(f"Version must be >= {minimum}.")
