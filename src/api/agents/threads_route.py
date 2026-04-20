"""Thread state inspection endpoints."""

from typing import Any

from fastapi import APIRouter

from src.api.agents.dependencies import get_app
from src.api.agents.schemas import ThreadStateResponse

router = APIRouter()


def _serialise_state(state: Any) -> ThreadStateResponse:
    """Convert a LangGraph StateSnapshot into a ThreadStateResponse."""
    if state is None:
        return ThreadStateResponse(values=None, next=[], tasks=[])
    values = state.values if hasattr(state, "values") else None
    next_nodes: list[str] = list(state.next) if hasattr(state, "next") else []
    tasks: list[dict[str, Any]] = []
    if hasattr(state, "tasks"):
        for t in state.tasks:
            tasks.append(t if isinstance(t, dict) else {"id": str(t)})
    return ThreadStateResponse(values=values, next=next_nodes, tasks=tasks)


@router.get("/{app_name}/threads/{thread_id}", response_model=ThreadStateResponse)
async def get_thread_state(
    app_name: str, thread_id: str
) -> ThreadStateResponse:
    """Return the current state snapshot for *thread_id*."""
    app = get_app(app_name)
    state = await app.aget_state(
        config={"configurable": {"thread_id": thread_id}}
    )
    return _serialise_state(state)


@router.get("/{app_name}/threads/{thread_id}/history")
async def get_thread_history(
    app_name: str, thread_id: str
) -> list[ThreadStateResponse]:
    """Return the full state history for *thread_id*."""
    app = get_app(app_name)
    history: list[ThreadStateResponse] = []
    async for state in app.aget_state_history(
        config={"configurable": {"thread_id": thread_id}}
    ):
        history.append(_serialise_state(state))
    return history
