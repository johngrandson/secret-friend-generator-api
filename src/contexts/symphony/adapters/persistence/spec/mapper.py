"""Mapping functions between Spec domain entity and SpecModel ORM row."""

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.adapters.persistence.spec.model import SpecModel


def to_entity(model: SpecModel) -> Spec:
    """Convert a SpecModel ORM row to a Spec domain entity."""
    return Spec(
        id=model.id,
        run_id=model.run_id,
        version=model.version,
        content=model.content,
        approved_at=model.approved_at,
        approved_by=model.approved_by,
        rejection_reason=model.rejection_reason,
        created_at=model.created_at,
    )


def to_model(spec: Spec) -> SpecModel:
    """Convert a Spec domain entity to a SpecModel ORM row."""
    return SpecModel(
        id=spec.id,
        run_id=spec.run_id,
        version=spec.version,
        content=spec.content,
        approved_at=spec.approved_at,
        approved_by=spec.approved_by,
        rejection_reason=spec.rejection_reason,
        created_at=spec.created_at,
    )
