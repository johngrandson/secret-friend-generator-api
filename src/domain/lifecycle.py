"""Domain lifecycle handler aggregator.

Single entry point to register all entity-level lifecycle handlers.
Call register_all_handlers() at app startup.
"""
from src.domain.group.handlers import register as register_group
from src.domain.participant.handlers import register as register_participant
from src.domain.secret_friend.handlers import register as register_secret_friend


def register_all_handlers() -> None:
    """Register lifecycle handlers for all domain entities.

    Each entity's register() connects its own handlers:
    side-effects, transactional cross-domain, and task relays.
    """
    register_group()
    register_participant()
    register_secret_friend()
