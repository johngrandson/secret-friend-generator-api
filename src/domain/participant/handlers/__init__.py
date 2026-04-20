"""Participant lifecycle handlers.

Composed from side-effects, transactional, and task relays.
"""

from src.domain.participant.handlers.side_effects import register_side_effects
from src.domain.participant.handlers.task_relays import register_task_relays
from src.domain.participant.handlers.transactional import register_transactional


def register() -> None:
    """Connect all participant lifecycle handlers to their signals."""
    register_side_effects()
    register_transactional()
    register_task_relays()
