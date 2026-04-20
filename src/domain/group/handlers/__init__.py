"""Group lifecycle handlers — composed from side-effects, transactional, and task relays."""
from src.domain.group.handlers.side_effects import register_side_effects
from src.domain.group.handlers.task_relays import register_task_relays
from src.domain.group.handlers.transactional import register_transactional


def register() -> None:
    """Connect all group lifecycle handlers to their signals."""
    register_side_effects()
    register_transactional()
    register_task_relays()
