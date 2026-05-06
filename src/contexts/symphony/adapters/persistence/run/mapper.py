"""Mapping functions between Run domain entity and RunModel ORM row."""

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.adapters.persistence.run.model import RunModel


def to_entity(model: RunModel) -> Run:
    """Convert a RunModel ORM row to a Run domain entity."""
    return Run(
        id=model.id,
        issue_id=model.issue_id,
        status=RunStatus(model.status),
        workspace_path=model.workspace_path,
        attempt=model.attempt,
        error=model.error,
        next_attempt_at=model.next_attempt_at,
        created_at=model.created_at,
    )


def to_model(run: Run) -> RunModel:
    """Convert a Run domain entity to a RunModel ORM row."""
    return RunModel(
        id=run.id,
        issue_id=run.issue_id,
        status=str(run.status),
        workspace_path=run.workspace_path,
        attempt=run.attempt,
        error=run.error,
        next_attempt_at=run.next_attempt_at,
        created_at=run.created_at,
    )
