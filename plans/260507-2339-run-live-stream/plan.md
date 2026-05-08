# Run Live Stream Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stream Claude Code agent events in real time from the backend to a dedicated `/runs/:runId/live` frontend page via Redis Pub/Sub + Server-Sent Events.

**Architecture:** A `RedisRunEventBus` adapter publishes each event from `ClaudeCodeRunner.run_turn` to a per-run Redis channel. A FastAPI SSE endpoint subscribes to that channel and streams events to the browser. The frontend opens an `EventSource` connection on a new dedicated page.

**Tech Stack:** Python `redis.asyncio`, FastAPI `StreamingResponse`, React `EventSource` API, `dependency_injector` container wiring.

**Spec:** `docs/superpowers/specs/2026-05-07-run-live-stream-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/infrastructure/config.py` | modify | add `REDIS_URL` setting |
| `src/infrastructure/adapters/events/redis_run_event_bus.py` | **create** | pub/sub publish + subscribe |
| `src/shared/agentic/agent_runner.py` | modify | add `AgentEventCallback` type + `on_event` to `IAgentRunner.run_turn` |
| `src/infrastructure/adapters/agent_runner/claude_code/runner.py` | modify | forward per-call `on_event` to `read_stream` |
| `src/contexts/symphony/use_cases/run/execute.py` | modify | accept `agent_event_hook`, create closure + sentinel |
| `src/contexts/symphony/adapters/http/run/routes/stream.py` | **create** | SSE endpoint `GET /runs/{run_id}/stream` |
| `src/contexts/symphony/adapters/http/run/routes/__init__.py` | modify | register stream route |
| `src/infrastructure/containers/symphony.py` | modify | wire `redis_event_bus` + `agent_event_hook` |
| `apps/web/src/pages/runs/run-live.tsx` | **create** | live stream page with `EventSource` |
| `apps/web/src/routes.tsx` | modify | add `/runs/:runId/live` route |
| `apps/web/src/pages/runs/runs-list.tsx` | modify | add "Live" link per run row |
| `tests/unit/infrastructure/adapters/events/test_redis_run_event_bus.py` | **create** | unit tests for event bus |
| `tests/unit/infrastructure/adapters/agent_runner/claude_code/test_claude_code_runner.py` | modify | tests for per-call `on_event` |
| `tests/unit/contexts/symphony/use_cases/run/test_execute.py` | modify | tests for `agent_event_hook` + sentinel |
| `tests/unit/contexts/symphony/adapters/http/run/test_stream_endpoint.py` | **create** | SSE generator unit test |

---

## Task 1 — `RedisRunEventBus` + `REDIS_URL` Setting

**Files:**
- Modify: `src/infrastructure/config.py`
- Create: `src/infrastructure/adapters/events/redis_run_event_bus.py`
- Create: `tests/unit/infrastructure/adapters/events/test_redis_run_event_bus.py`
- Create: `tests/unit/infrastructure/adapters/events/__init__.py`

- [ ] **Step 1.1 — Write failing tests**

Create `tests/unit/infrastructure/adapters/events/__init__.py` (empty).

Create `tests/unit/infrastructure/adapters/events/test_redis_run_event_bus.py`:

```python
"""Unit tests for RedisRunEventBus — mocked Redis client, no live server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus


@pytest.fixture
def run_id():
    return uuid4()


@pytest.mark.asyncio
async def test_publish_sends_json_to_redis_channel(run_id):
    mock_client = AsyncMock()
    bus = object.__new__(RedisRunEventBus)
    bus._client = mock_client

    await bus.publish(run_id, {"type": "assistant", "text": "hello"})

    mock_client.publish.assert_awaited_once_with(
        f"run:{run_id}:events",
        json.dumps({"type": "assistant", "text": "hello"}),
    )


@pytest.mark.asyncio
async def test_publish_is_noop_when_client_is_none(run_id):
    bus = RedisRunEventBus(redis_url=None)
    # Must not raise
    await bus.publish(run_id, {"type": "test"})


def test_init_creates_no_client_for_memory_url():
    bus = RedisRunEventBus(redis_url="memory://")
    assert bus._client is None


def test_init_creates_no_client_when_url_is_none():
    bus = RedisRunEventBus(redis_url=None)
    assert bus._client is None


def test_channel_name_includes_run_id(run_id):
    bus = RedisRunEventBus(redis_url=None)
    assert bus._channel(run_id) == f"run:{run_id}:events"
```

- [ ] **Step 1.2 — Run tests to confirm they fail**

```bash
cd /home/joao/CodeHorizon/python-ai-starter
poetry run pytest tests/unit/infrastructure/adapters/events/test_redis_run_event_bus.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` for `redis_run_event_bus`.

- [ ] **Step 1.3 — Add `REDIS_URL` to Settings**

In `src/infrastructure/config.py`, add one field after `CELERY_RESULT_BACKEND`:

```python
REDIS_URL: str | None = None
"""Redis URL for the run event bus (real-time agent event streaming).

When None, the event bus is a no-op and streaming is disabled. In
production set to the same URL as ``CELERY_BROKER_URL``. In tests the
default ``None`` disables the feature without needing a live server."""
```

- [ ] **Step 1.4 — Implement `RedisRunEventBus`**

Create `src/infrastructure/adapters/events/redis_run_event_bus.py`:

```python
"""Redis Pub/Sub event bus for per-run agent event streaming.

``publish`` sends each claude CLI event to a per-run channel.
``subscribe`` yields events from that channel as an async generator.

Both methods are no-ops when ``redis_url`` is None or not a redis:// URL
so execution continues normally when the feature is disabled (tests, local
without Redis).
"""

import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis


class RedisRunEventBus:
    def __init__(self, redis_url: str | None = None) -> None:
        self._client: aioredis.Redis | None = None
        if redis_url and redis_url.startswith("redis"):
            self._client = aioredis.from_url(redis_url, decode_responses=True)

    def _channel(self, run_id: UUID) -> str:
        return f"run:{run_id}:events"

    async def publish(self, run_id: UUID, event: dict[str, Any]) -> None:
        if self._client is None:
            return
        await self._client.publish(self._channel(run_id), json.dumps(event))

    async def subscribe(self, run_id: UUID) -> AsyncGenerator[dict[str, Any], None]:
        if self._client is None:
            return
        pubsub = self._client.pubsub()
        await pubsub.subscribe(self._channel(run_id))
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                event: dict[str, Any] = json.loads(message["data"])
                yield event
                if event.get("type") == "_stream_done":
                    break
        finally:
            await pubsub.unsubscribe(self._channel(run_id))
```

- [ ] **Step 1.5 — Run tests, confirm they pass**

```bash
poetry run pytest tests/unit/infrastructure/adapters/events/test_redis_run_event_bus.py -v
```

Expected: 5 tests pass.

- [ ] **Step 1.6 — Commit**

```bash
git add src/infrastructure/config.py \
        src/infrastructure/adapters/events/redis_run_event_bus.py \
        tests/unit/infrastructure/adapters/events/__init__.py \
        tests/unit/infrastructure/adapters/events/test_redis_run_event_bus.py
git commit -m "feat(events): RedisRunEventBus pub/sub adapter + REDIS_URL setting"
```

---

## Task 2 — Extend `IAgentRunner.run_turn` + `ClaudeCodeRunner`

**Files:**
- Modify: `src/shared/agentic/agent_runner.py`
- Modify: `src/infrastructure/adapters/agent_runner/claude_code/runner.py`
- Modify: `tests/unit/infrastructure/adapters/agent_runner/claude_code/test_claude_code_runner.py`

- [ ] **Step 2.1 — Write failing tests**

Append to `tests/unit/infrastructure/adapters/agent_runner/claude_code/test_claude_code_runner.py`:

```python
@pytest.mark.asyncio
async def test_run_turn_fires_per_call_on_event():
    """on_event passed to run_turn receives each stream event."""
    events_received: list[dict] = []

    async def callback(event: dict) -> None:
        events_received.append(event)

    lines = [
        _assistant_line("hello"),
        _result_line(session_id="s1"),
    ]
    proc = _FakeProcess(lines=lines)
    runner = ClaudeCodeRunner(
        config=ClaudeCodeConfig(turn_timeout_ms=5000, stall_timeout_ms=2000),
        process_factory=_factory_from(proc),
    )

    await runner.run_turn(prompt="hi", workspace=Path("/tmp"), on_event=callback)

    assert any(e.get("type") == "assistant" for e in events_received)


@pytest.mark.asyncio
async def test_run_turn_per_call_on_event_takes_priority_over_constructor():
    """on_event in run_turn overrides the constructor-level on_event."""
    constructor_events: list[dict] = []
    call_events: list[dict] = []

    async def constructor_cb(event: dict) -> None:
        constructor_events.append(event)

    async def call_cb(event: dict) -> None:
        call_events.append(event)

    lines = [_assistant_line("x"), _result_line(session_id="s2")]
    proc = _FakeProcess(lines=lines)
    runner = ClaudeCodeRunner(
        config=ClaudeCodeConfig(turn_timeout_ms=5000, stall_timeout_ms=2000),
        process_factory=_factory_from(proc),
        on_event=constructor_cb,
    )

    await runner.run_turn(prompt="hi", workspace=Path("/tmp"), on_event=call_cb)

    assert len(call_events) > 0
    assert len(constructor_events) == 0
```

Note: `ClaudeCodeConfig` needs to be imported. Check what's already imported in the test file; if missing, add:
```python
from src.infrastructure.adapters.workflow import ClaudeCodeConfig
```
(Already imported as `_config()` helper — use that wrapper instead if preferred.)

- [ ] **Step 2.2 — Run tests to confirm they fail**

```bash
poetry run pytest tests/unit/infrastructure/adapters/agent_runner/claude_code/test_claude_code_runner.py::test_run_turn_fires_per_call_on_event -v
```

Expected: `TypeError` — `run_turn()` got unexpected keyword argument `on_event`.

- [ ] **Step 2.3 — Add `AgentEventCallback` to `IAgentRunner`**

In `src/shared/agentic/agent_runner.py`, add after the imports block:

```python
from collections.abc import Awaitable, Callable
from typing import Any

AgentEventCallback = Callable[[dict[str, Any]], Awaitable[None] | None]
```

Extend `IAgentRunner.run_turn` signature:

```python
class IAgentRunner(Protocol):
    """Run one conversational turn against an agent backend."""

    async def run_turn(
        self,
        *,
        prompt: str,
        workspace: Path,
        session_id: str | None = None,
        on_event: "AgentEventCallback | None" = None,
    ) -> TurnResult: ...
```

Also add `AgentEventCallback` to `__all__` if there is one, or simply export it.

- [ ] **Step 2.4 — Update `ClaudeCodeRunner.run_turn` + `_run_turn_inner`**

In `src/infrastructure/adapters/agent_runner/claude_code/runner.py`, change `run_turn` to accept and forward `on_event`:

```python
async def run_turn(
    self,
    *,
    prompt: str,
    workspace: Path,
    session_id: str | None = None,
    on_event: EventCallback | None = None,
) -> TurnResult:
    """Run one ``claude`` CLI turn and return the aggregated result."""
    validate_prompt(prompt)
    args = build_args(prompt=prompt, config=self._config, session_id=session_id)
    turn_seconds = self._config.turn_timeout_ms / 1000.0
    effective_on_event = on_event or self._on_event
    try:
        return await asyncio.wait_for(
            self._run_turn_inner(args, workspace, effective_on_event),
            timeout=turn_seconds,
        )
    except TimeoutError as err:
        raise ClaudeCodeTimeoutError(
            f"Turn timeout after {self._config.turn_timeout_ms}ms",
            kind="turn",
        ) from err
```

Change `_run_turn_inner` signature to accept `on_event`:

```python
async def _run_turn_inner(
    self, args: Sequence[str], cwd: Path, on_event: EventCallback | None
) -> TurnResult:
    proc = await self._factory(args, cwd)
    state = TurnState()
    try:
        await read_stream(
            proc, state, self._config.stall_timeout_ms, on_event
        )
        exit_code = await proc.wait()
    finally:
        if proc.returncode is None:
            proc.kill()
            try:
                await asyncio.wait_for(proc.wait(), timeout=KILL_TIMEOUT_SECONDS)
            except TimeoutError:
                log.warning("Claude process did not exit after kill")

    if (
        state.is_error
        and state.error_message
        and "user input" in state.error_message
    ):
        raise ClaudeCodeInputRequiredError(state.error_message)
    if exit_code != 0:
        raise ClaudeCodeExitError(
            f"Claude CLI exited with status {exit_code}", exit_code=exit_code
        )
    if state.is_error:
        raise ClaudeCodeResultError(state.error_message or "unknown result error")

    return TurnResult(
        session_id=state.session_id,
        usage=state.usage,
        text="".join(state.text_parts),
        is_error=False,
        error_message=None,
    )
```

- [ ] **Step 2.5 — Update `_FakeAgentRunner` in `test_execute.py`**

In `tests/unit/contexts/symphony/use_cases/run/test_execute.py`, extend `_FakeAgentRunner.run_turn` to accept the new optional param:

```python
async def run_turn(
    self,
    *,
    prompt: str,
    workspace: Path,
    session_id: str | None = None,
    on_event=None,  # satisfies updated IAgentRunner signature
) -> TurnResult:
    self.calls.append(
        {"prompt": prompt, "workspace": workspace, "session_id": session_id}
    )
    if self._raises is not None:
        raise self._raises
    assert self._result is not None
    return self._result
```

- [ ] **Step 2.6 — Run tests**

```bash
poetry run pytest tests/unit/infrastructure/adapters/agent_runner/claude_code/ -v
poetry run pytest tests/unit/contexts/symphony/use_cases/run/test_execute.py -v
```

Expected: all pass.

- [ ] **Step 2.7 — Commit**

```bash
git add src/shared/agentic/agent_runner.py \
        src/infrastructure/adapters/agent_runner/claude_code/runner.py \
        tests/unit/infrastructure/adapters/agent_runner/claude_code/test_claude_code_runner.py \
        tests/unit/contexts/symphony/use_cases/run/test_execute.py
git commit -m "feat(runner): add per-call on_event to IAgentRunner.run_turn + ClaudeCodeRunner"
```

---

## Task 3 — Extend `ExecuteRunUseCase` with `agent_event_hook`

**Files:**
- Modify: `src/contexts/symphony/use_cases/run/execute.py`
- Modify: `tests/unit/contexts/symphony/use_cases/run/test_execute.py`

- [ ] **Step 3.1 — Write failing tests**

Append to `tests/unit/contexts/symphony/use_cases/run/test_execute.py`:

```python
@pytest.mark.asyncio
async def test_execute_calls_agent_event_hook_with_run_id(uow, tmp_path):
    """agent_event_hook receives (run_id, event) for each agent event."""
    hook_calls: list[tuple] = []

    async def hook(run_id, event):
        hook_calls.append((run_id, event))

    run = _make_run(tmp_path)
    run_id = run.id
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run_id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run_id)
    uow.runs.update.return_value = run

    runner = _FakeAgentRunner(result=TurnResult(session_id="x"))
    use_case = ExecuteRunUseCase(
        uow=uow,
        agent_runner=runner,
        event_publisher=FakePublisher(),
        agent_event_hook=hook,
    )

    await use_case.execute(
        ExecuteRunRequest(
            run_id=run_id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
        )
    )

    # Sentinel must always be the last call
    sentinel_calls = [(rid, ev) for rid, ev in hook_calls if ev.get("type") == "_stream_done"]
    assert len(sentinel_calls) == 1
    assert sentinel_calls[0][0] == run_id


@pytest.mark.asyncio
async def test_execute_publishes_sentinel_even_on_runner_failure(uow, tmp_path):
    """_stream_done is published even when the agent runner raises."""
    hook_calls: list[tuple] = []

    async def hook(run_id, event):
        hook_calls.append((run_id, event))

    run = _make_run(tmp_path)
    run_id = run.id
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run_id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run_id)
    uow.runs.update.return_value = run

    runner = _FakeAgentRunner(raises=AgentRunnerError("boom"))
    use_case = ExecuteRunUseCase(
        uow=uow,
        agent_runner=runner,
        event_publisher=FakePublisher(),
        agent_event_hook=hook,
    )

    await use_case.execute(
        ExecuteRunRequest(
            run_id=run_id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
        )
    )

    assert any(ev.get("type") == "_stream_done" for _, ev in hook_calls)


@pytest.mark.asyncio
async def test_execute_works_without_hook(uow, tmp_path):
    """agent_event_hook=None — no change to existing behaviour."""
    run = _make_run(tmp_path)
    run_id = run.id
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run_id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run_id)
    uow.runs.update.return_value = run

    runner = _FakeAgentRunner(result=TurnResult(session_id="x"))
    use_case = ExecuteRunUseCase(
        uow=uow,
        agent_runner=runner,
        event_publisher=FakePublisher(),
    )

    result = await use_case.execute(
        ExecuteRunRequest(
            run_id=run_id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
        )
    )

    assert result.outcome == ExecuteOutcome.SUCCESS
```

- [ ] **Step 3.2 — Run to confirm failure**

```bash
poetry run pytest tests/unit/contexts/symphony/use_cases/run/test_execute.py::test_execute_calls_agent_event_hook_with_run_id -v
```

Expected: `TypeError` — `ExecuteRunUseCase.__init__()` got unexpected keyword argument `agent_event_hook`.

- [ ] **Step 3.3 — Implement in `execute.py`**

At the top of `src/contexts/symphony/use_cases/run/execute.py`, add imports:

```python
from collections.abc import Awaitable, Callable
from typing import Any

AgentEventHook = Callable[[UUID, dict[str, Any]], Awaitable[None]]
```

Modify `ExecuteRunUseCase.__init__`:

```python
def __init__(
    self,
    uow: ISymphonyUnitOfWork,
    agent_runner: IAgentRunner,
    event_publisher: IEventPublisher,
    agent_event_hook: AgentEventHook | None = None,
) -> None:
    self._uow = uow
    self._agent_runner = agent_runner
    self._publisher = event_publisher
    self._agent_event_hook = agent_event_hook
```

Modify `execute()` — replace the `run_turn` call block and add sentinel publishing. The full relevant section becomes:

```python
async def execute(self, request: ExecuteRunRequest) -> ExecuteRunResponse:
    response: ExecuteRunResponse
    events: list[DomainEvent] = []
    _run_id_for_sentinel: UUID | None = None

    async with self._uow:
        run = await self._uow.runs.find_by_id(request.run_id)
        if run is None:
            return ExecuteRunResponse(
                None, ExecuteOutcome.FAILED, error_message="Run not found."
            )
        ensure_run_status(
            run,
            RunStatus.PLAN_APPROVED,
            action="ExecuteRun",
            error_class=InvalidRunStateError,
        )
        workspace_path = ensure_workspace_set(run, error_class=InvalidRunStateError)

        spec = await self._uow.specs.find_latest_for_run(run.id)
        if spec is None or spec.approved_at is None:
            return ExecuteRunResponse(
                None,
                ExecuteOutcome.FAILED,
                error_message="No approved spec for run.",
            )
        plan = await self._uow.plans.find_latest_for_run(run.id)
        if plan is None or plan.approved_at is None:
            return ExecuteRunResponse(
                None,
                ExecuteOutcome.FAILED,
                error_message="No approved plan for run.",
            )

        prompt = render_run_prompt(
            template=request.prompt_template,
            issue=request.issue,
            spec_content=spec.content,
            plan_content=plan.content,
            attempt=run.attempt,
        )

        session = AgentSession.create(run_id=run.id, model=request.model_name)
        run.set_status(RunStatus.EXECUTE)

        _run_id_for_sentinel = run.id

        async def _on_event(event: dict[str, Any]) -> None:
            if self._agent_event_hook:
                await self._agent_event_hook(run.id, event)

        try:
            turn = await self._agent_runner.run_turn(
                prompt=prompt,
                workspace=Path(workspace_path),
                session_id=session.session_id,
                on_event=_on_event if self._agent_event_hook else None,
            )
        except AgentRunnerError as exc:
            response, events = await self._build_failure_response(
                exc=exc,
                run=run,
                session=session,
                retry_config=request.retry_config,
            )
        else:
            response, events = await self._build_success_response(
                turn=turn, run=run, session=session
            )

        await self._uow.commit()

    if self._agent_event_hook and _run_id_for_sentinel:
        await self._agent_event_hook(_run_id_for_sentinel, {"type": "_stream_done"})

    if events:
        await self._publisher.publish(events)
    return response
```

Note: also add `from typing import Any` to imports if not present, and `UUID` is already imported.

- [ ] **Step 3.4 — Run all execute tests**

```bash
poetry run pytest tests/unit/contexts/symphony/use_cases/run/test_execute.py -v
```

Expected: all tests pass (including the 3 new + existing).

- [ ] **Step 3.5 — Commit**

```bash
git add src/contexts/symphony/use_cases/run/execute.py \
        tests/unit/contexts/symphony/use_cases/run/test_execute.py
git commit -m "feat(execute): add agent_event_hook for real-time run event streaming"
```

---

## Task 4 — SSE Endpoint

**Files:**
- Create: `src/contexts/symphony/adapters/http/run/routes/stream.py`
- Modify: `src/contexts/symphony/adapters/http/run/routes/__init__.py`
- Create: `tests/unit/contexts/symphony/adapters/http/run/__init__.py`
- Create: `tests/unit/contexts/symphony/adapters/http/run/test_stream_endpoint.py`

- [ ] **Step 4.1 — Write failing test for the SSE generator**

Create `tests/unit/contexts/symphony/adapters/http/run/__init__.py` (empty).

Create `tests/unit/contexts/symphony/adapters/http/run/test_stream_endpoint.py`:

```python
"""Unit tests for the SSE generator used by GET /runs/{run_id}/stream."""

import json
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest

from src.contexts.symphony.adapters.http.run.routes.stream import _sse_generator


class _MockBus:
    """Fake RedisRunEventBus for testing the generator."""

    def __init__(self, events: list[dict]) -> None:
        self._events = events

    async def subscribe(self, run_id) -> AsyncGenerator[dict, None]:
        for event in self._events:
            yield event


@pytest.mark.asyncio
async def test_sse_generator_yields_data_lines():
    events = [{"type": "assistant", "text": "hello"}, {"type": "_stream_done"}]
    bus = _MockBus(events)
    run_id = uuid4()

    chunks = []
    async for chunk in _sse_generator(bus, run_id):
        chunks.append(chunk)

    assert chunks[0] == f"data: {json.dumps(events[0])}\n\n"
    assert chunks[1] == f"data: {json.dumps(events[1])}\n\n"


@pytest.mark.asyncio
async def test_sse_generator_yields_all_events():
    events = [{"type": "assistant"}, {"type": "result"}, {"type": "_stream_done"}]
    bus = _MockBus(events)

    chunks = []
    async for chunk in _sse_generator(bus, uuid4()):
        chunks.append(chunk)

    assert len(chunks) == 3


@pytest.mark.asyncio
async def test_sse_generator_empty_bus():
    """No-op bus (client is None) yields nothing."""

    class _EmptyBus:
        async def subscribe(self, run_id) -> AsyncGenerator[dict, None]:
            return
            yield  # noqa: unreachable — makes this an async generator

    chunks = []
    async for chunk in _sse_generator(_EmptyBus(), uuid4()):
        chunks.append(chunk)

    assert chunks == []
```

- [ ] **Step 4.2 — Run to confirm failure**

```bash
poetry run pytest tests/unit/contexts/symphony/adapters/http/run/test_stream_endpoint.py -v
```

Expected: `ImportError` — cannot import `_sse_generator`.

- [ ] **Step 4.3 — Implement the SSE endpoint**

Create `src/contexts/symphony/adapters/http/run/routes/stream.py`:

```python
"""GET /runs/{run_id}/stream — Server-Sent Events endpoint.

Subscribes to the Redis pub/sub channel for the given run and streams
each agent event as an SSE ``data:`` line. The stream ends when the
``_stream_done`` sentinel arrives (published by ``ExecuteRunUseCase``)
or when the client disconnects.
"""

import json
from collections.abc import AsyncGenerator
from typing import Annotated, Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from fastapi.responses import StreamingResponse

from src.contexts.symphony.adapters.http.run.router import router
from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus
from src.infrastructure.containers import Container


async def _sse_generator(
    bus: Any, run_id: UUID
) -> AsyncGenerator[str, None]:
    async for event in bus.subscribe(run_id):
        yield f"data: {json.dumps(event)}\n\n"


@inject
def _get_event_bus(
    bus: RedisRunEventBus = Depends(Provide[Container.symphony.redis_event_bus]),
) -> RedisRunEventBus:
    return bus


RedisEventBusDep = Annotated[RedisRunEventBus, Depends(_get_event_bus)]


@router.get("/{run_id}/stream")
async def stream_run_events(
    run_id: UUID, bus: RedisEventBusDep
) -> StreamingResponse:
    return StreamingResponse(
        content=_sse_generator(bus, run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 4.4 — Register the route**

In `src/contexts/symphony/adapters/http/run/routes/__init__.py`, add:

```python
import src.contexts.symphony.adapters.http.run.routes.stream  # noqa: F401
```

- [ ] **Step 4.5 — Run tests**

```bash
poetry run pytest tests/unit/contexts/symphony/adapters/http/run/test_stream_endpoint.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 4.6 — Commit**

```bash
git add src/contexts/symphony/adapters/http/run/routes/stream.py \
        src/contexts/symphony/adapters/http/run/routes/__init__.py \
        tests/unit/contexts/symphony/adapters/http/run/__init__.py \
        tests/unit/contexts/symphony/adapters/http/run/test_stream_endpoint.py
git commit -m "feat(http): SSE endpoint GET /runs/{run_id}/stream for live agent events"
```

---

## Task 5 — DI Container Wiring

**Files:**
- Modify: `src/infrastructure/containers/symphony.py`

- [ ] **Step 5.1 — Add `redis_event_bus` and `agent_event_hook` to `SymphonyContainer`**

In `src/infrastructure/containers/symphony.py`, add imports near the top:

```python
from src.contexts.symphony.use_cases.run.execute import AgentEventHook
from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus
```

Add factory helper after `_build_gate_runner`:

```python
def _make_agent_event_hook(bus: RedisRunEventBus) -> AgentEventHook:
    return bus.publish
```

Inside `SymphonyContainer`, add two new providers after `gate_runner`:

```python
redis_event_bus = providers.Singleton(
    RedisRunEventBus,
    redis_url=config.provided.REDIS_URL,
)

agent_event_hook = providers.Factory(
    _make_agent_event_hook,
    bus=redis_event_bus,
)
```

Update `execute_run_use_case` to include `agent_event_hook`:

```python
execute_run_use_case = providers.Factory(
    ExecuteRunUseCase,
    uow=symphony_uow,
    agent_runner=agent_runner,
    event_publisher=event_publisher,
    agent_event_hook=agent_event_hook,
)
```

- [ ] **Step 5.2 — Run existing container + integration tests**

```bash
poetry run pytest tests/unit/infrastructure/containers/ -v
poetry run pytest tests/integration/ -v --timeout=30
```

Expected: all pass. If there are import-linter violations, see Step 5.3.

- [ ] **Step 5.3 — Run architecture checks**

```bash
poetry run lint-imports
poetry run pytest tests/architecture/ -v
poetry run ruff check src/
poetry run mypy src/
```

Fix any violations before committing. Common issue: `redis_run_event_bus` importing from outside allowed layers — check `.importlinter` contracts.

- [ ] **Step 5.4 — Commit**

```bash
git add src/infrastructure/containers/symphony.py
git commit -m "feat(container): wire RedisRunEventBus and agent_event_hook into symphony DI"
```

---

## Task 6 — Frontend: Live Stream Page

**Files:**
- Create: `apps/web/src/pages/runs/run-live.tsx`
- Modify: `apps/web/src/routes.tsx`
- Modify: `apps/web/src/pages/runs/runs-list.tsx`

No backend tests. Verify visually in the browser after implementing.

- [ ] **Step 6.1 — Create `run-live.tsx`**

Create `apps/web/src/pages/runs/run-live.tsx`:

```tsx
// Live stream page for a single run — connects via EventSource (SSE).

import { useEffect, useRef, useState } from "react"
import { useParams } from "react-router-dom"

type AgentEvent = { type: string; [key: string]: unknown }
type StreamStatus = "connecting" | "live" | "ended" | "error"

export function RunLive() {
  const { runId } = useParams<{ runId: string }>()
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [status, setStatus] = useState<StreamStatus>("connecting")
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!runId) return

    const es = new EventSource(`/api/runs/${runId}/stream`)

    es.onopen = () => setStatus("live")

    es.onmessage = (e) => {
      const event = JSON.parse(e.data as string) as AgentEvent
      if (event.type === "_stream_done") {
        setStatus("ended")
        es.close()
        return
      }
      setEvents((prev) => [...prev, event])
    }

    es.onerror = () => {
      if (status !== "ended") setStatus("error")
    }

    return () => es.close()
  }, [runId])

  // Auto-scroll to bottom on new event
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events])

  const statusColors: Record<StreamStatus, string> = {
    connecting: "bg-yellow-100 text-yellow-800",
    live: "bg-green-100 text-green-800",
    ended: "bg-zinc-100 text-zinc-600",
    error: "bg-red-100 text-red-700",
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold font-mono">
          Run {runId?.slice(0, 8)}… — Live Stream
        </h1>
        <span
          className={`text-xs px-2 py-0.5 rounded font-medium ${statusColors[status]}`}
        >
          {status}
        </span>
      </div>

      <div className="flex-1 font-mono text-xs bg-zinc-950 text-zinc-100 rounded-lg p-4 overflow-auto">
        {events.length === 0 && status === "connecting" && (
          <p className="text-zinc-500">Waiting for agent events…</p>
        )}
        {events.map((event, i) => (
          <pre
            key={i}
            className="whitespace-pre-wrap mb-2 border-b border-zinc-800 pb-2"
          >
            {JSON.stringify(event, null, 2)}
          </pre>
        ))}
        <div ref={bottomRef} />
      </div>

      {status === "ended" && (
        <p className="text-sm text-zinc-500">Stream ended — run complete.</p>
      )}
    </div>
  )
}
```

- [ ] **Step 6.2 — Add route to `routes.tsx`**

In `apps/web/src/routes.tsx`, add the import:

```tsx
import { RunLive } from "@/pages/runs/run-live"
```

Add the route entry inside the `children` array, after the existing `runs/:runId` entry:

```tsx
{ path: "runs/:runId/live", element: <RunLive /> },
```

- [ ] **Step 6.3 — Add "Live" link in `runs-list.tsx`**

In `apps/web/src/pages/runs/runs-list.tsx`, import `Link` is already present. Find the `<Td>` block containing the delete button (around line 172) and add a "Live" link before the delete `<Button>`:

```tsx
<Td>
  <div className="flex gap-2">
    <Link
      to={`/runs/${run.id}/live`}
      className="text-xs text-blue-600 hover:underline"
    >
      Live
    </Link>
    <Button
      variant="danger"
      onClick={() => {
        if (confirm(`Delete run ${run.issue_id}? This cannot be undone.`)) {
          deleteRun.mutate(run.id)
        }
      }}
    >
      Delete
    </Button>
  </div>
</Td>
```

(Wrap the existing `<Button>` in the `<div>` and add the `<Link>` before it.)

- [ ] **Step 6.4 — Start the dev server and verify**

```bash
cd apps/web && npm run dev
```

1. Navigate to `/runs` — confirm "Live" link appears per run row.
2. Click "Live" on any run — confirm page loads at `/runs/:id/live` with "connecting" status.
3. While a run is being orchestrated, confirm events appear in real time.
4. After run completes, confirm status changes to "ended".

- [ ] **Step 6.5 — Commit**

```bash
git add apps/web/src/pages/runs/run-live.tsx \
        apps/web/src/routes.tsx \
        apps/web/src/pages/runs/runs-list.tsx
git commit -m "feat(web): run live stream page with EventSource SSE connection"
```

---

## Task 7 — Final Validation

- [ ] **Step 7.1 — Run full architecture check**

```bash
bash scripts/verify-arch.sh
```

Expected: clean exit (all 5 checks pass).

- [ ] **Step 7.2 — Run full test suite**

```bash
poetry run pytest -q
```

Expected: all tests pass. Count should be ≥ previous baseline + new tests from this plan.

- [ ] **Step 7.3 — Check import-linter contracts for new files**

```bash
poetry run lint-imports
```

If any contract is broken by `redis_run_event_bus.py` importing `redis.asyncio` in an unexpected layer, it's correct — `redis.asyncio` is infra. Verify no domain or use-case layer has a new redis import.

- [ ] **Step 7.4 — Commit final state (if any fixes applied)**

```bash
git add -A
git commit -m "fix(arch): resolve any import-linter or mypy issues from live stream feature"
```

---

## Architecture Compliance Checklist

Before marking complete:

- [ ] `RedisRunEventBus` lives in `infrastructure/adapters/events/` (infra layer) ✓
- [ ] `ExecuteRunUseCase` receives `agent_event_hook: Callable` — no infra import ✓
- [ ] SSE route lives in `symphony/adapters/http/` (HTTP adapter layer) ✓
- [ ] No cross-context imports introduced ✓
- [ ] `AgentEventCallback` added to `shared/agentic/` — shared kernel ✓
- [ ] `poetry run lint-imports` clean ✓
- [ ] `pytest tests/architecture/` clean ✓
