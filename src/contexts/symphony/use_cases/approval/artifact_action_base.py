"""artifact-action-base — shared approve/reject logic for Plan and Spec use-cases."""

from dataclasses import dataclass
from typing import Protocol, TypeVar
from uuid import UUID

from src.contexts.symphony.domain.approval.aggregate import ApprovedAggregate
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.shared.event_publisher import IEventPublisher

# Generic in the aggregate type so concrete repos (IPlanRepository,
# ISpecRepository) satisfy the Protocol with their concrete aggregate.
# Invariant because update() takes the aggregate as input (must match exactly).
_AggT = TypeVar("_AggT", bound=ApprovedAggregate)


class _ApprovableRepo(Protocol[_AggT]):
    """Minimal repository contract for ApprovedAggregate (Plan/Spec)."""

    async def find_by_id(self, artifact_id: UUID) -> _AggT | None: ...
    async def update(self, artifact: _AggT) -> _AggT: ...


@dataclass
class ArtifactActionResult:
    """Intermediate result returned by run_approve/reject_artifact helpers."""

    artifact: ApprovedAggregate | None
    success: bool
    error_message: str | None = None


async def run_approve_artifact(
    *,
    uow: ISymphonyUnitOfWork,
    publisher: IEventPublisher,
    repo: _ApprovableRepo[_AggT],
    artifact_id: UUID,
    approved_by: str,
    not_found_msg: str,
) -> ArtifactActionResult:
    """Execute the approve flow for any ApprovedAggregate repository."""
    async with uow:
        artifact = await repo.find_by_id(artifact_id)
        if artifact is None:
            return ArtifactActionResult(None, False, not_found_msg)
        try:
            artifact.approve(by=approved_by)
        except ValueError as exc:
            return ArtifactActionResult(None, False, str(exc))
        updated = await repo.update(artifact)
        await uow.commit()
        events = artifact.pull_events()

    if events:  # pragma: no branch
        await publisher.publish(events)
    return ArtifactActionResult(updated, True)


async def run_reject_artifact(
    *,
    uow: ISymphonyUnitOfWork,
    publisher: IEventPublisher,
    repo: _ApprovableRepo[_AggT],
    artifact_id: UUID,
    reason: str,
    not_found_msg: str,
) -> ArtifactActionResult:
    """Execute the reject flow for any ApprovedAggregate repository."""
    async with uow:
        artifact = await repo.find_by_id(artifact_id)
        if artifact is None:
            return ArtifactActionResult(None, False, not_found_msg)
        try:
            artifact.reject(reason=reason)
        except ValueError as exc:
            return ArtifactActionResult(None, False, str(exc))
        updated = await repo.update(artifact)
        await uow.commit()
        events = artifact.pull_events()

    if events:  # pragma: no branch
        await publisher.publish(events)
    return ArtifactActionResult(updated, True)
