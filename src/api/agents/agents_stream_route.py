"""POST /{app_name}/stream — Server-Sent Events streaming endpoint."""

import json
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk

from src.api.agents.agents_dependencies import get_app
from src.api.agents.agents_schemas import InvokeBody

log = logging.getLogger(__name__)

router = APIRouter()


async def _event_generator(
    app: Any,
    messages: list[dict[str, Any]],
    thread_id: str,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted lines from the app stream."""
    try:
        stream = app.astream(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        )
        async for chunk, metadata in stream:
            node = (metadata or {}).get("langgraph_node", "unknown")
            if isinstance(chunk, AIMessageChunk):
                event: dict[str, Any] = {
                    "type": "token",
                    "content": chunk.content,
                    "node": node,
                }
            elif hasattr(chunk, "content"):
                event = {"type": "message", "content": chunk.content, "node": node}
            else:
                continue
            yield f"data: {json.dumps(event)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception:
        log.exception("Stream error for app=%s thread=%s", app, thread_id)
        error_event = json.dumps({"type": "error", "content": "Internal stream error"})
        yield f"data: {error_event}\n\n"


@router.post("/{app_name}/stream")
async def stream(app_name: str, body: InvokeBody) -> StreamingResponse:
    """Stream tokens/messages from *app_name* as Server-Sent Events."""
    app = get_app(app_name)
    messages = [m.model_dump() for m in body.messages]
    return StreamingResponse(
        _event_generator(app, messages, body.thread_id),
        media_type="text/event-stream",
    )
