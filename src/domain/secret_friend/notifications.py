"""Secret friend notification handlers — pure business logic, no infrastructure deps."""
import logging

log = logging.getLogger(__name__)


def on_secret_friend_assigned(*, assignment_id: int, group_id: int) -> None:
    """Handle secret-friend-assigned notification."""
    log.info("notification: secret friend assigned — id=%s group_id=%s", assignment_id, group_id)


def on_secret_friend_deleted(*, secret_friend_id: int) -> None:
    """Handle secret-friend-deleted notification."""
    log.info("notification: secret friend deleted — id=%s", secret_friend_id)
