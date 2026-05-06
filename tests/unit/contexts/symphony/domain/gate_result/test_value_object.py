"""Unit tests for the GateResult VO."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.gate_result.value_object import (
    OUTPUT_MAX_LEN,
    GateResult,
)
from src.shared.agentic.gate import GateName, GateStatus


def test_is_frozen() -> None:
    gr = GateResult(
        run_id=uuid4(), gate_name=GateName("ci"), status=GateStatus.PASSED
    )
    with pytest.raises(FrozenInstanceError):
        gr.duration_ms = 999  # type: ignore[misc]


def test_output_truncated_to_max_length() -> None:
    long_output = "x" * (OUTPUT_MAX_LEN + 100)
    gr = GateResult(
        run_id=uuid4(),
        gate_name=GateName("ci"),
        status=GateStatus.FAILED,
        output=long_output,
    )
    assert len(gr.output) == OUTPUT_MAX_LEN


def test_negative_duration_raises() -> None:
    with pytest.raises(ValueError):
        GateResult(
            run_id=uuid4(),
            gate_name=GateName("ci"),
            status=GateStatus.PASSED,
            duration_ms=-5,
        )


def test_default_id_and_created_at_populate() -> None:
    gr = GateResult(
        run_id=uuid4(), gate_name=GateName("ci"), status=GateStatus.PASSED
    )
    assert gr.id is not None
    assert gr.created_at is not None
