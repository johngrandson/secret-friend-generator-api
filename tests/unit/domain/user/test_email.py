"""Unit tests for the Email value object."""

import pytest

from src.domain.user.email import Email


def test_valid_email_is_created():
    email = Email("user@example.com")
    assert email.value == "user@example.com"


def test_str_returns_value():
    email = Email("user@example.com")
    assert str(email) == "user@example.com"


def test_email_is_frozen():
    email = Email("user@example.com")
    with pytest.raises((AttributeError, TypeError)):
        email.value = "other@example.com"  # type: ignore[misc]


def test_equal_emails_are_equal():
    assert Email("a@b.com") == Email("a@b.com")


def test_different_emails_are_not_equal():
    assert Email("a@b.com") != Email("c@d.com")


@pytest.mark.parametrize(
    "bad",
    [
        "not-an-email",
        "@nodomain.com",
        "no-at-sign",
        "",
        "spaces in@email.com",
    ],
)
def test_invalid_email_raises(bad: str):
    with pytest.raises(ValueError):
        Email(bad)
