"""GET /runs/{run_id}/stream — Server-Sent Events live agent event stream.

Subscribes to the per-run Redis Pub/Sub channel and yields each event as
an SSE data line. Closes automatically when the _stream_done sentinel
arrives or the client disconnects.
"""

import json
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi.responses import StreamingResponse

from src.contexts.symphony.adapters.http.run.deps import RedisRunEventBusDep
from src.contexts.symphony.adapters.http.run.router import router
from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus


async def _build_sse_generator(
    run_id: UUID,
    bus: RedisRunEventBus,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted lines from the run event channel.

    Emits a leading SSE comment so dev proxies (Vite, nginx) flush response
    headers immediately — without it EventSource.onopen never fires until
    the first real event arrives.
    """
    yield ": ready\n\n"
    async for event in bus.subscribe(run_id):
        yield f"data: {json.dumps(event)}\n\n"
        if event.get("type") == "_stream_done":
            break


@router.get("/{run_id}/stream")
async def stream_run_events(
    run_id: UUID,
    bus: RedisRunEventBusDep,
) -> StreamingResponse:
    """Stream real-time agent events for a run via Server-Sent Events."""
    return StreamingResponse(
        content=_build_sse_generator(run_id, bus),
        media_type="text/event-stream",
    )
