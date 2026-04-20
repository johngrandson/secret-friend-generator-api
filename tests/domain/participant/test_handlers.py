"""Tests for participant domain handlers (side-effects, task relays, transactional)."""

import logging
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate
from src.domain.group.service import GroupService
from src.domain.participant.schemas import (
    ParticipantCreate,
    ParticipantStatus,
)
from src.domain.participant.service import ParticipantService
from src.domain.participant.signals import participant_created, participant_deleted
from src.domain.secret_friend.service import SecretFriendService


# ── Side-effect handler tests ────────────────────────────────────────────────


def test_on_participant_created_logs_event(
    db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    from src.domain.participant.handlers.side_effects import (
        _on_participant_created,
        register_side_effects,
    )

    group = GroupService.create(GroupCreate(name="Log Group", description="d"), db_session)
    register_side_effects()
    try:
        with caplog.at_level(
            logging.INFO, logger="src.domain.participant.handlers.side_effects"
        ):
            ParticipantService.create(
                ParticipantCreate(name="Dave", group_id=group.id), db_session
            )

        assert any("participant created" in r.message for r in caplog.records)
    finally:
        participant_created.disconnect(_on_participant_created)


# ── Task relay handler tests ─────────────────────────────────────────────────


def test_relay_participant_created_dispatches_task(db_session: Session) -> None:
    group = GroupService.create(
        GroupCreate(name="Relay Group", description="d"), db_session
    )

    with patch(
        "src.domain.participant.handlers.task_relays.dispatch_task"
    ) as mock_dispatch:
        from src.domain.participant.handlers.task_relays import (
            _relay_participant_created,
            register_task_relays,
        )

        register_task_relays()
        try:
            participant = ParticipantService.create(
                ParticipantCreate(name="Eve", group_id=group.id), db_session
            )
            mock_dispatch.assert_called_once_with(
                "notifications.participant_joined",
                participant_id=participant.id,
                group_id=group.id,
            )
        finally:
            participant_created.disconnect(_relay_participant_created)


def test_relay_participant_deleted_dispatches_task(db_session: Session) -> None:
    group = GroupService.create(
        GroupCreate(name="Relay Group", description="d"), db_session
    )
    participant = ParticipantService.create(
        ParticipantCreate(name="Frank", group_id=group.id), db_session
    )

    with patch(
        "src.domain.participant.handlers.task_relays.dispatch_task"
    ) as mock_dispatch:
        from src.domain.participant.handlers.task_relays import (
            _relay_participant_deleted,
            register_task_relays,
        )

        register_task_relays()
        try:
            ParticipantService.delete(participant.id, db_session)
            mock_dispatch.assert_called_once_with(
                "notifications.participant_deleted", participant_id=participant.id
            )
        finally:
            participant_deleted.disconnect(_relay_participant_deleted)


# ── Transactional handler test ───────────────────────────────────────────────


def test_reveal_participant_on_assignment_changes_status_to_revealed(
    db_session: Session,
) -> None:
    """THE critical integration test.

    After SecretFriendService.assign(), the assigning participant's status must
    transition from PENDING to REVEALED via the transactional handler that listens
    to the secret_friend_assigned signal.
    """
    from src.domain.participant.handlers.transactional import (
        _reveal_participant_on_assignment,
        register_transactional,
    )
    from src.domain.secret_friend.signals import secret_friend_assigned

    register_transactional()
    try:
        group = GroupService.create(
            GroupCreate(name="Assignment Group", description="d"), db_session
        )
        alice = ParticipantService.create(
            ParticipantCreate(name="Alice", group_id=group.id), db_session
        )
        ParticipantService.create(
            ParticipantCreate(name="Bob", group_id=group.id), db_session
        )

        # Precondition: Alice starts as PENDING
        assert alice.status == ParticipantStatus.PENDING

        SecretFriendService.assign(
            group_id=group.id, participant_id=alice.id, db_session=db_session
        )

        updated = ParticipantService.get_by_id(alice.id, db_session)
        assert updated.status == ParticipantStatus.REVEALED
    finally:
        secret_friend_assigned.disconnect(_reveal_participant_on_assignment)
