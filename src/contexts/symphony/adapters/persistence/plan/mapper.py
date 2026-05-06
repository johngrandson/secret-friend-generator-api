"""Mapping functions between Plan domain entity and PlanModel ORM row."""

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.adapters.persistence.plan.model import PlanModel


def to_entity(model: PlanModel) -> Plan:
    """Convert a PlanModel ORM row to a Plan domain entity."""
    return Plan(
        id=model.id,
        run_id=model.run_id,
        version=model.version,
        content=model.content,
        approved_at=model.approved_at,
        approved_by=model.approved_by,
        rejection_reason=model.rejection_reason,
        created_at=model.created_at,
    )


def to_model(plan: Plan) -> PlanModel:
    """Convert a Plan domain entity to a PlanModel ORM row."""
    return PlanModel(
        id=plan.id,
        run_id=plan.run_id,
        version=plan.version,
        content=plan.content,
        approved_at=plan.approved_at,
        approved_by=plan.approved_by,
        rejection_reason=plan.rejection_reason,
        created_at=plan.created_at,
    )
