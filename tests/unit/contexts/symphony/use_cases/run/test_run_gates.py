"""Unit tests for RunGatesUseCase."""

from pathlib import Path

import pytest

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import (
    GatesCompleted,
    RunStatusChanged,
)
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.use_cases.run.run_gates import (
    InvalidRunStateForGatesError,
    RunGatesRequest,
    RunGatesUseCase,
    _compute_all_passed,
)
from src.shared.agentic.gate import GateName, GateOutcome, GateRunner, GateStatus
from tests.conftest import FakePublisher, FakeSymphonyUoW


class _ScriptedGateRunner(GateRunner):
    """GateRunner stub that returns canned outcomes."""

    def __init__(self, outcomes: list[GateOutcome]) -> None:
        super().__init__([])
        self._outcomes = outcomes
        self.run_all_calls: list[dict] = []

    async def run_all(self, *, workspace: Path, config: object) -> list[GateOutcome]:
        self.run_all_calls.append({"workspace": workspace, "config": config})
        return list(self._outcomes)


def _make_executed_run(workspace: Path) -> Run:
    run = Run.create(issue_id="ENG-7")
    for status in (
        RunStatus.GEN_SPEC,
        RunStatus.SPEC_PENDING,
        RunStatus.SPEC_APPROVED,
        RunStatus.GEN_PLAN,
        RunStatus.PLAN_PENDING,
        RunStatus.PLAN_APPROVED,
        RunStatus.EXECUTE,
        RunStatus.EXECUTED,
    ):
        run.set_status(status, workspace_path=str(workspace))
    run.pull_events()
    return run


def _outcome(name: str, status: GateStatus, *, output: str = "") -> GateOutcome:
    return GateOutcome(
        name=GateName(name),
        status=status,
        output=output,
        duration_ms=10,
    )


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


async def test_run_gates_all_passed(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_executed_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.gate_results.save_batch.side_effect = lambda results: results

    runner = _ScriptedGateRunner(
        [_outcome("ci", GateStatus.PASSED, output="all good")]
    )
    use_case = RunGatesUseCase(
        uow=uow, gate_runner=runner, event_publisher=publisher
    )

    resp = await use_case.execute(
        RunGatesRequest(run_id=run.id, harness_config=object())
    )

    assert resp.success is True
    assert resp.all_passed is True
    assert run.status == RunStatus.GATES_PASSED
    types = {type(e) for e in publisher.published}
    assert RunStatusChanged in types
    assert GatesCompleted in types
    uow.gate_results.save_batch.assert_called_once()


async def test_run_gates_one_failed_marks_gates_failed(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_executed_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.gate_results.save_batch.side_effect = lambda results: results

    runner = _ScriptedGateRunner(
        [
            _outcome("ci", GateStatus.PASSED),
            _outcome("coverage", GateStatus.FAILED, output="<80%"),
        ]
    )
    use_case = RunGatesUseCase(
        uow=uow, gate_runner=runner, event_publisher=publisher
    )

    resp = await use_case.execute(
        RunGatesRequest(run_id=run.id, harness_config=object())
    )

    assert resp.all_passed is False
    assert run.status == RunStatus.GATES_FAILED


async def test_run_gates_skipped_outcomes_dont_block_pass(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_executed_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.gate_results.save_batch.side_effect = lambda results: results

    runner = _ScriptedGateRunner(
        [
            _outcome("ci", GateStatus.PASSED),
            _outcome("coverage", GateStatus.SKIPPED),
        ]
    )
    use_case = RunGatesUseCase(
        uow=uow, gate_runner=runner, event_publisher=publisher
    )

    resp = await use_case.execute(
        RunGatesRequest(run_id=run.id, harness_config=object())
    )

    assert resp.all_passed is True
    assert run.status == RunStatus.GATES_PASSED


async def test_run_gates_run_not_found(
    uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    uow.runs.find_by_id.return_value = None
    runner = _ScriptedGateRunner([])
    use_case = RunGatesUseCase(
        uow=uow, gate_runner=runner, event_publisher=publisher
    )

    resp = await use_case.execute(
        RunGatesRequest(run_id=run_id_not_used(), harness_config=object())
    )
    assert resp.success is False
    assert "not found" in (resp.error_message or "").lower()


async def test_run_gates_wrong_status_raises(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = Run.create(issue_id="ENG-X")
    run.set_status(RunStatus.GEN_SPEC, workspace_path=str(tmp_path))
    run.pull_events()
    uow.runs.find_by_id.return_value = run

    runner = _ScriptedGateRunner([])
    use_case = RunGatesUseCase(
        uow=uow, gate_runner=runner, event_publisher=publisher
    )

    with pytest.raises(InvalidRunStateForGatesError):
        await use_case.execute(
            RunGatesRequest(run_id=run.id, harness_config=object())
        )


def test_compute_all_passed_no_outcomes_passes() -> None:
    assert _compute_all_passed([]) is True


def test_compute_all_passed_skipped_only_passes() -> None:
    assert _compute_all_passed([_outcome("ci", GateStatus.SKIPPED)]) is True


def test_compute_all_passed_one_failure_blocks() -> None:
    outcomes = [
        _outcome("ci", GateStatus.PASSED),
        _outcome("cov", GateStatus.FAILED),
    ]
    assert _compute_all_passed(outcomes) is False


# Helpers ---------------------------------------------------------------


def run_id_not_used():
    from uuid import uuid4

    return uuid4()
