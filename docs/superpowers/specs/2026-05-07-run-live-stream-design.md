# Run Live Stream — Design Spec

**Date:** 2026-05-07  
**Status:** Approved  
**Scope:** Real-time streaming of Claude Code agent events to a dedicated frontend page, using Redis Pub/Sub + Server-Sent Events.

---

## Problem

When a Run is orchestrated (`POST /runs/{id}/orchestrate`), the `ClaudeCodeRunner` emits a continuous stream of events from the `claude` CLI (text blocks, tool calls, usage, etc.). Currently these events are consumed only internally — no visibility from the browser.

---

## Solution Overview

Wire a Redis Pub/Sub channel between the Celery execution path and a new FastAPI SSE endpoint. The frontend subscribes via `EventSource` on a dedicated live page.

```
POST /runs/{id}/orchestrate
  → ExecuteRunUseCase(agent_event_hook=redis_bus.publish)
    → ClaudeCodeRunner.run_turn(on_event=lambda e: hook(run.id, e))
      → PUBLISH "run:{run_id}:events"

GET /api/runs/{id}/stream   (SSE)
  → redis_bus.subscribe(run_id)
  → StreamingResponse (text/event-stream)
  → data: {…}\n\n

Browser EventSource → /runs/:runId/live
```

---

## Constraints & Decisions

- **No replay on reconnect.** Browser reconnects receive events from that moment only. Redis Pub/Sub has no persistence, which is acceptable given this decision.
- **1 run at a time.** No multi-run dashboard.
- **New dedicated page** at `/runs/:runId/live`, not a tab inside run-detail.
- **Redis already in stack** (`redis ^7.4.0`). No new dependencies.
- **SSE over WebSocket.** Unidirectional, works through Vite proxy without extra config.
- **Orchestration runs via HTTP** (`POST /orchestrate` → FastAPI DI container). The Celery `dispatch_runner.py` only starts runs, does not execute them — so no changes needed there.

---

## Backend Changes

### 1. `src/infrastructure/config.py`

Add one optional setting:

```python
REDIS_URL: str | None = None
```

Falls back to parsing `CELERY_BROKER_URL` when `None`. When `CELERY_BROKER_URL` is `memory://` (test/local), the event bus becomes a no-op — execution continues normally without publishing.

### 2. `src/infrastructure/adapters/events/redis_run_event_bus.py` *(new)*

```python
class RedisRunEventBus:
    async def publish(self, run_id: UUID, event: dict) -> None
    async def subscribe(self, run_id: UUID) -> AsyncGenerator[dict, None]
```

- `publish`: `PUBLISH run:{run_id}:events <json>`. No-op if Redis unavailable.
- `subscribe`: creates a pub/sub subscriber, yields each parsed event dict. Used by the SSE endpoint.
- Graceful degradation: if Redis URL resolves to `None` / `memory://`, both methods no-op without raising.

### 3. `src/shared/agentic/agent_runner.py`

Add type alias and extend `IAgentRunner.run_turn` signature:

```python
AgentEventCallback = Callable[[dict[str, Any]], Awaitable[None] | None]

class IAgentRunner(Protocol):
    async def run_turn(
        self,
        *,
        prompt: str,
        workspace: Path,
        session_id: str | None = None,
        on_event: AgentEventCallback | None = None,   # NEW — optional
    ) -> TurnResult: ...
```

Backward-compatible: all existing call sites that omit `on_event` continue to work.

### 4. `src/infrastructure/adapters/agent_runner/claude_code/runner.py`

`run_turn` forwards the per-call `on_event` to `read_stream`, taking priority over the constructor's `self._on_event`:

```python
effective_on_event = on_event or self._on_event
await read_stream(proc, state, self._config.stall_timeout_ms, effective_on_event)
```

### 5. `src/contexts/symphony/use_cases/run/execute.py`

Accept optional hook (callable, not an infra import):

```python
AgentEventHook = Callable[[UUID, dict], Awaitable[None]]

class ExecuteRunUseCase:
    def __init__(
        self,
        ...,
        agent_event_hook: AgentEventHook | None = None,
    ) -> None: ...
```

Before calling `run_turn`, create a per-run closure:

```python
async def _on_event(event: dict) -> None:
    if self._agent_event_hook:
        await self._agent_event_hook(run.id, event)
```

After the run completes (success or failure), publish a sentinel so the frontend knows to stop:

```python
await self._agent_event_hook(run.id, {"type": "_stream_done"})
```

### 6. `src/contexts/symphony/adapters/http/run/routes/stream.py` *(new)*

```
GET /runs/{run_id}/stream
```

- Returns `StreamingResponse(content=generator, media_type="text/event-stream")`
- Generator calls `redis_bus.subscribe(run_id)` and yields `data: <json>\n\n` per event
- Stops when it receives `{"type": "_stream_done"}` or the client disconnects

### 7. `src/contexts/symphony/adapters/http/run/routes/__init__.py`

Register the new stream route alongside existing routes.

### 8. `src/infrastructure/containers/symphony.py`

```python
redis_event_bus = providers.Singleton(RedisRunEventBus, redis_url=config.provided.REDIS_URL)

def _make_agent_event_hook(bus: RedisRunEventBus) -> AgentEventHook:
    return bus.publish

agent_event_hook = providers.Factory(_make_agent_event_hook, bus=redis_event_bus)

execute_run_use_case = providers.Factory(
    ExecuteRunUseCase,
    ...,
    agent_event_hook=agent_event_hook,
)
```

---

## Frontend Changes

### 9. `apps/web/src/pages/runs/run-live.tsx` *(new)*

- Reads `:runId` from route params
- `useEffect`: opens `new EventSource("/api/runs/{runId}/stream")`
- State: `events: object[]` — appended on each `onmessage`
- Renders a scrolling log; auto-scrolls to bottom on new event
- Shows status indicator (connecting / live / ended)
- On `{"type": "_stream_done"}`, closes `EventSource` and marks stream as ended
- Cleans up `EventSource` on unmount

### 10. `apps/web/src/routes.tsx`

```tsx
{ path: "runs/:runId/live", element: <RunLive /> }
```

### 11. `apps/web/src/pages/runs/runs-list.tsx`

Add a "Live" icon/link per run row that navigates to `/runs/:runId/live`.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Redis unavailable at publish | No-op; run continues normally |
| Redis unavailable at subscribe | SSE endpoint returns empty stream or 503 |
| Client disconnects | Generator exits; Redis subscription released |
| Run errors/fails | `_stream_done` sentinel still published from `execute.py` finally block |
| `EventSource` network error | Browser auto-reconnects (EventSource default behavior); no replay |

---

## Architecture Compliance

- `RedisRunEventBus` lives in `infrastructure/adapters/events/` — infra layer ✓
- `ExecuteRunUseCase` receives `agent_event_hook: Callable` — no infra import in use case ✓
- SSE endpoint lives in `symphony/adapters/http/` — HTTP adapter layer ✓
- No cross-context imports introduced ✓
- `AgentEventCallback` type added to `shared/agentic/` — shared kernel ✓

---

## Files Summary

| File | Action |
|---|---|
| `src/infrastructure/config.py` | modify |
| `src/infrastructure/adapters/events/redis_run_event_bus.py` | **create** |
| `src/shared/agentic/agent_runner.py` | modify |
| `src/infrastructure/adapters/agent_runner/claude_code/runner.py` | modify |
| `src/contexts/symphony/use_cases/run/execute.py` | modify |
| `src/contexts/symphony/adapters/http/run/routes/stream.py` | **create** |
| `src/contexts/symphony/adapters/http/run/routes/__init__.py` | modify |
| `src/infrastructure/containers/symphony.py` | modify |
| `apps/web/src/pages/runs/run-live.tsx` | **create** |
| `apps/web/src/routes.tsx` | modify |
| `apps/web/src/pages/runs/runs-list.tsx` | modify |

**Total: 3 new files, 8 modified.**

---

## Out of Scope

- Replay on reconnect
- Multi-run dashboard
- Persistence of event stream
- Streaming in `generate_spec` / `generate_plan` use cases (same pattern, future work)
- Authentication/authorization on SSE endpoint (same as existing endpoints)
