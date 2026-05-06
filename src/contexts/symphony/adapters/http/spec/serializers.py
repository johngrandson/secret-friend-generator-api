"""Serialization helpers — SpecDTO → JSON-serialisable dict."""

from src.contexts.symphony.use_cases.spec.dto import SpecDTO


def to_spec_output(dto: SpecDTO) -> dict:
    """Serialize a SpecDTO to a plain dict for JSON responses."""
    return {
        "id": str(dto.id),
        "run_id": str(dto.run_id),
        "version": dto.version,
        "content": dto.content,
        "approved_at": dto.approved_at.isoformat() if dto.approved_at else None,
        "approved_by": dto.approved_by,
        "rejection_reason": dto.rejection_reason,
        "created_at": dto.created_at.isoformat(),
    }
