"""Shared signal infrastructure — the isolated decorator.

Domain-specific signals live in their respective entity modules:
- domain/group/signals.py
- domain/participant/signals.py
- domain/secret_friend/signals.py
"""
import functools
import logging
from collections.abc import Callable
from typing import ParamSpec, TypeVar

log = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def isolated(fn: Callable[P, R]) -> Callable[P, R | None]:
    """Decorator for lifecycle handlers — isolates exceptions.

    Blinker's send() propagates handler exceptions by design.
    This decorator catches and logs failures so a side-effect
    handler (Slack, email, logging) never crashes the domain
    service that emitted the signal.
    """

    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            return fn(*args, **kwargs)
        except Exception:
            log.exception("lifecycle handler failed: %s", fn.__qualname__)
            return None

    return wrapper
