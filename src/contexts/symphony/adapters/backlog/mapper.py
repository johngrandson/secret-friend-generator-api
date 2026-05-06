"""Normalization helpers — convert raw Linear GraphQL nodes into domain Issue VOs."""

from datetime import datetime
from typing import Any

from src.contexts.symphony.domain.backlog.errors import BacklogSchemaError
from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority

BLOCKED_BY_RELATION = "blocks"


def normalize_linear_issue(node: dict[str, Any]) -> Issue:
    """Normalize a Linear GraphQL issue node into a domain Issue VO.

    Raises:
        BacklogSchemaError: payload shape does not match expectations
            (missing required field, malformed sub-object, unknown
            priority value, etc.).
    """
    state_obj = node.get("state")
    if not isinstance(state_obj, dict) or "name" not in state_obj:
        raise BacklogSchemaError(
            f"Linear issue missing state.name; got {state_obj!r}"
        )

    labels_container = node.get("labels") or {}
    labels: tuple[str, ...] = tuple(
        n["name"]
        for n in labels_container.get("nodes", [])
        if isinstance(n, dict) and "name" in n
    )

    inverse_container = node.get("inverseRelations") or {}
    blocked_by: tuple[str, ...] = tuple(
        n["issue"]["identifier"]
        for n in inverse_container.get("nodes", [])
        if isinstance(n, dict)
        and n.get("type") == BLOCKED_BY_RELATION
        and isinstance(n.get("issue"), dict)
        and "identifier" in n["issue"]
    )

    try:
        priority_raw = node.get("priority", 0)
        try:
            priority = IssuePriority(int(priority_raw))
        except ValueError as err:
            raise BacklogSchemaError(
                f"Linear issue unknown priority value: {priority_raw!r}"
            ) from err

        raw_updated_at = node.get("updatedAt")
        updated_at: datetime | None = (
            datetime.fromisoformat(raw_updated_at) if raw_updated_at else None
        )

        return Issue(
            identifier=node["identifier"],
            title=node["title"],
            description=node.get("description") or "",
            priority=priority,
            state=state_obj["name"],
            branch_name=node.get("branchName"),
            url=node.get("url"),
            labels=labels,
            blocked_by=blocked_by,
            created_at=datetime.fromisoformat(node["createdAt"]),
            updated_at=updated_at,
        )
    except KeyError as err:
        field = err.args[0] if err.args else "<unknown>"
        raise BacklogSchemaError(
            f"Linear issue missing required field: {field}"
        ) from err
