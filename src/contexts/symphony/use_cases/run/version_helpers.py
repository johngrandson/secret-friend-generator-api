"""Shared version-bump helper for write-once aggregates (Spec, Plan).

Both generate use cases compute ``(previous.version + 1) if previous else 1``;
this is the same one-liner expressed once and typed against any aggregate
that exposes a ``version`` attribute.
"""

from typing import Protocol

from src.contexts.symphony.domain.constants import MIN_ARTIFACT_VERSION


class HasVersion(Protocol):
    """Anything with an integer ``version`` attribute."""

    @property
    def version(self) -> int: ...


def next_version(previous: HasVersion | None) -> int:
    """Return ``previous.version + 1`` or ``MIN_ARTIFACT_VERSION`` when none."""
    if previous is None:
        return MIN_ARTIFACT_VERSION
    return previous.version + 1
