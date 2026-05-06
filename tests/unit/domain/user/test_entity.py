"""Unit tests for the User entity."""

import pytest

from src.domain.user.email import Email
from src.domain.user.entity import User
from src.domain.user.events import UserCreated, UserDeactivated, UserUpdated


def _email(value: str = "test@example.com") -> Email:
    return Email(value)


def test_create_returns_active_user():
    user = User.create(email=_email(), name="Alice")
    assert user.name == "Alice"
    assert user.is_active is True
    assert user.id is not None


def test_create_blank_name_raises():
    with pytest.raises(ValueError):
        User.create(email=_email(), name="   ")


def test_deactivate_sets_is_active_false():
    user = User.create(email=_email(), name="Bob")
    user.pull_events()  # clear creation event
    user.deactivate()
    assert user.is_active is False


def test_activate_sets_is_active_true():
    user = User.create(email=_email(), name="Bob")
    user.deactivate()
    user.activate()
    assert user.is_active is True


def test_can_login_true_when_active():
    user = User.create(email=_email(), name="Carol")
    assert user.can_login() is True


def test_can_login_false_when_inactive():
    user = User.create(email=_email(), name="Carol")
    user.deactivate()
    assert user.can_login() is False


def test_update_name_changes_name():
    user = User.create(email=_email(), name="Dave")
    user.update_name("David")
    assert user.name == "David"


def test_update_name_blank_raises():
    user = User.create(email=_email(), name="Eve")
    with pytest.raises(ValueError):
        user.update_name("  ")


def test_create_collects_user_created_event():
    user = User.create(email=_email("new@example.com"), name="Alice")
    events = user.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], UserCreated)
    assert events[0].user_id == user.id
    assert events[0].email == "new@example.com"
    assert events[0].name == "Alice"


def test_pull_events_clears_after_read():
    user = User.create(email=_email(), name="Alice")
    user.pull_events()
    assert user.pull_events() == []


def test_deactivate_collects_user_deactivated_event():
    user = User.create(email=_email(), name="Bob")
    user.pull_events()  # clear creation event
    user.deactivate()
    events = user.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], UserDeactivated)
    assert events[0].user_id == user.id


def test_deactivate_already_inactive_does_not_collect_event():
    user = User.create(email=_email(), name="Bob")
    user.deactivate()
    user.pull_events()  # clear both events
    user.deactivate()   # already inactive — no new event
    assert user.pull_events() == []


def test_update_name_collects_user_updated_event():
    user = User.create(email=_email(), name="Carol")
    user.pull_events()  # clear creation event
    user.update_name("Caroline")
    events = user.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], UserUpdated)
    assert events[0].user_id == user.id


def test_update_name_same_value_does_not_collect_event():
    user = User.create(email=_email(), name="Carol")
    user.pull_events()
    user.update_name("Carol")  # no change
    assert user.pull_events() == []
