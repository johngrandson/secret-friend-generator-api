"""Unit tests for the code-host VOs (CreatedPR, ExistingPR)."""

import pytest

from src.contexts.symphony.domain.code_host import CreatedPR, ExistingPR


def test_created_pr_accepts_valid_fields() -> None:
    pr = CreatedPR(number=42, url="https://github.com/x/y/pull/42")
    assert pr.number == 42
    assert pr.url.endswith("/42")


def test_created_pr_rejects_blank_url() -> None:
    with pytest.raises(ValueError, match="url"):
        CreatedPR(number=1, url="   ")


def test_created_pr_rejects_negative_number() -> None:
    with pytest.raises(ValueError, match="number"):
        CreatedPR(number=-1, url="https://example.com")


def test_existing_pr_carries_draft_flag() -> None:
    pr = ExistingPR(
        number=7, url="https://github.com/x/y/pull/7", is_draft=True
    )
    assert pr.is_draft is True


def test_existing_pr_validates_url() -> None:
    with pytest.raises(ValueError):
        ExistingPR(number=7, url="", is_draft=False)
