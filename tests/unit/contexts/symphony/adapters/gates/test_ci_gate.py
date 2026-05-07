"""Unit tests for CIGate — runs ``ci_command`` via real bash subprocess.

CIGate uses the workspace adapter's ``exec_hook`` helper, which itself
spawns ``bash -c <script>``. These tests run actual bash scripts in the
pytest tmp_path so behaviour is exercised end-to-end without mocking
the subprocess layer.
"""

from pathlib import Path

import pytest

from src.contexts.symphony.adapters.gates.ci import (
    MAX_OUTPUT_CHARS,
    CIGate,
    _truncate_tail,
)
from src.infrastructure.adapters.workflow import HarnessConfig
from src.shared.agentic.gate import GateName, GateStatus


def _harness(ci_command: str) -> HarnessConfig:
    return HarnessConfig(ci_command=ci_command)


@pytest.mark.asyncio
async def test_ci_gate_passes_when_command_succeeds(tmp_path: Path) -> None:
    gate = CIGate(timeout_seconds=10)
    outcome = await gate.run(
        workspace=tmp_path, config=_harness("echo all-good && exit 0")
    )
    assert outcome.status == GateStatus.PASSED
    assert outcome.name == GateName("ci")
    assert "all-good" in outcome.output
    assert outcome.metadata_json["exit_code"] == 0


@pytest.mark.asyncio
async def test_ci_gate_fails_when_command_returns_nonzero(tmp_path: Path) -> None:
    gate = CIGate(timeout_seconds=10)
    outcome = await gate.run(
        workspace=tmp_path, config=_harness("echo failed && exit 7")
    )
    assert outcome.status == GateStatus.FAILED
    assert outcome.metadata_json["exit_code"] == 7
    assert "failed" in outcome.output


@pytest.mark.asyncio
async def test_ci_gate_returns_failed_on_timeout(tmp_path: Path) -> None:
    gate = CIGate(timeout_seconds=0.1)
    outcome = await gate.run(workspace=tmp_path, config=_harness("sleep 5"))
    assert outcome.status == GateStatus.FAILED
    assert outcome.metadata_json["reason"] == "timeout"
    assert "timed out" in outcome.output


@pytest.mark.asyncio
async def test_ci_gate_truncates_long_output(tmp_path: Path) -> None:
    """Long stdout is truncated from the head; the tail (the recent lines) is kept."""
    cmd = "yes 'noisy' | head -c 200000"  # ~200KB of repeated text
    gate = CIGate(timeout_seconds=10)
    outcome = await gate.run(workspace=tmp_path, config=_harness(cmd))
    assert outcome.status == GateStatus.PASSED
    assert len(outcome.output) <= MAX_OUTPUT_CHARS


def test_truncate_tail_keeps_marker_and_recent() -> None:
    big = "abc" * 5000
    out = _truncate_tail(big, 100)
    assert "[...truncated head...]" in out
    assert len(out) <= 100
    assert out.endswith("c")  # tail of "abc" sequence


def test_truncate_tail_passthrough_when_under_limit() -> None:
    assert _truncate_tail("short", 100) == "short"
