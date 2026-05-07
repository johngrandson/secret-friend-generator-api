"""Unit tests for the SPEC content validator."""

import pytest

from src.contexts.symphony.use_cases.spec.validate import (
    REQUIRED_SECTIONS,
    SpecStructureError,
    validate_spec_content,
)

VALID_SPEC = """
## Goals
- thing one

## Non-Goals
- not this

## Constraints
- limit

## Approach
narrative
"""


def test_validate_spec_content_accepts_complete_spec() -> None:
    validate_spec_content(VALID_SPEC)


def test_validate_spec_content_rejects_missing_goals() -> None:
    bad = VALID_SPEC.replace("## Goals", "## NotGoals")
    with pytest.raises(SpecStructureError, match="Goals"):
        validate_spec_content(bad)


def test_validate_spec_content_lists_all_missing_sections() -> None:
    with pytest.raises(SpecStructureError) as exc:
        validate_spec_content("just text, no headers")
    msg = str(exc.value)
    for section in REQUIRED_SECTIONS:
        assert section in msg


def test_validate_spec_content_empty_string_raises() -> None:
    with pytest.raises(SpecStructureError):
        validate_spec_content("")
