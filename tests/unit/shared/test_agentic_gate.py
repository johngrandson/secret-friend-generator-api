"""Unit tests for src.shared.agentic.gate."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import ClassVar

import pytest

from src.shared.agentic.gate import (
    Gate,
    GateName,
    GateOutcome,
    GateRunner,
    GateStatus,
)


class _PassGate(Gate[None]):
    name: ClassVar[GateName] = GateName("pass")
    is_blocking: ClassVar[bool] = True

    async def run(self, *, workspace: Path, config: None) -> GateOutcome:
        return GateOutcome(name=self.name, status=GateStatus.PASSED, duration_ms=10)


class _FailGate(Gate[None]):
    name: ClassVar[GateName] = GateName("fail")
    is_blocking: ClassVar[bool] = True

    async def run(self, *, workspace: Path, config: None) -> GateOutcome:
        return GateOutcome(
            name=self.name, status=GateStatus.FAILED, output="boom", duration_ms=5
        )


class _RaisingGate(Gate[None]):
    name: ClassVar[GateName] = GateName("raising")
    is_blocking: ClassVar[bool] = False

    async def run(self, *, workspace: Path, config: None) -> GateOutcome:
        raise RuntimeError("internal")


class _NonBlockingFail(Gate[None]):
    name: ClassVar[GateName] = GateName("nb")
    is_blocking: ClassVar[bool] = False

    async def run(self, *, workspace: Path, config: None) -> GateOutcome:
        return GateOutcome(name=self.name, status=GateStatus.FAILED)


class TestGateOutcome:
    def test_is_frozen(self) -> None:
        outcome = GateOutcome(name=GateName("ci"), status=GateStatus.PASSED)
        with pytest.raises(FrozenInstanceError):
            outcome.duration_ms = 99  # type: ignore[misc]

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(ValueError):
            GateOutcome(
                name=GateName("ci"), status=GateStatus.PASSED, duration_ms=-1
            )


class TestGateRunner:
    @pytest.mark.asyncio
    async def test_runs_all_when_all_pass(self, tmp_path: Path) -> None:
        runner = GateRunner([_PassGate(), _PassGate()])
        outcomes = await runner.run_all(workspace=tmp_path, config=None)
        assert [o.status for o in outcomes] == [GateStatus.PASSED, GateStatus.PASSED]

    @pytest.mark.asyncio
    async def test_blocking_failure_skips_subsequent(self, tmp_path: Path) -> None:
        runner = GateRunner([_FailGate(), _PassGate()])
        outcomes = await runner.run_all(workspace=tmp_path, config=None)
        assert outcomes[0].status == GateStatus.FAILED
        assert outcomes[1].status == GateStatus.SKIPPED
        assert outcomes[1].metadata_json["skipped_due_to"] == "fail"

    @pytest.mark.asyncio
    async def test_non_blocking_failure_does_not_short_circuit(
        self, tmp_path: Path
    ) -> None:
        runner = GateRunner([_NonBlockingFail(), _PassGate()])
        outcomes = await runner.run_all(workspace=tmp_path, config=None)
        assert outcomes[0].status == GateStatus.FAILED
        assert outcomes[1].status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_raising_gate_becomes_failed_outcome(
        self, tmp_path: Path
    ) -> None:
        runner = GateRunner([_RaisingGate(), _PassGate()])
        outcomes = await runner.run_all(workspace=tmp_path, config=None)
        assert outcomes[0].status == GateStatus.FAILED
        assert "RuntimeError" in outcomes[0].metadata_json["exception_type"]
        # Non-blocking, so next still runs.
        assert outcomes[1].status == GateStatus.PASSED

    def test_is_blocking_lookup(self) -> None:
        runner = GateRunner([_PassGate(), _NonBlockingFail()])
        assert runner.is_blocking(GateName("pass")) is True
        assert runner.is_blocking(GateName("nb")) is False
        assert runner.is_blocking(GateName("unknown")) is False
