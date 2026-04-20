"""Lifecycle handlers — side-effects triggered by domain signals.

Equivalent to Phoenix's user_lifecycle_action/3. Handlers are
registered via @signal.connect decorator and fire automatically
when a service emits the corresponding signal.

Import this module at app startup to ensure handlers are registered.
"""
import logging

from src.domain.shared.signals import (
    group_created,
    participant_created,
    participant_updated,
    secret_friend_assigned,
)

log = logging.getLogger(__name__)


@group_created.connect
def on_group_created(sender, **kwargs):
    group = kwargs.get("group")
    log.info("lifecycle: group created — id=%s name=%s", group.id, group.name)


@participant_created.connect
def on_participant_created(sender, **kwargs):
    participant = kwargs.get("participant")
    log.info(
        "lifecycle: participant created — id=%s group_id=%s",
        participant.id,
        participant.group_id,
    )


@participant_updated.connect
def on_participant_updated(sender, **kwargs):
    participant = kwargs.get("participant")
    log.info(
        "lifecycle: participant updated — id=%s status=%s",
        participant.id,
        participant.status,
    )


@secret_friend_assigned.connect
def on_secret_friend_assigned(sender, **kwargs):
    group_id = kwargs.get("group_id")
    participant_id = kwargs.get("participant_id")
    log.info(
        "lifecycle: secret friend assigned — group_id=%s participant_id=%s",
        group_id,
        participant_id,
    )
