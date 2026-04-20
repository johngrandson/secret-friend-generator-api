# Signals & Lifecycle Handlers Architecture

Pattern inspired by Phoenix/Elixir's `user_lifecycle_action/3`. Uses [blinker](https://blinker.readthedocs.io/) for in-process event dispatch.

## Structure

```
src/domain/
├── group/
│   ├── signals.py      # group_created
│   └── handlers.py     # side-effect handlers + register()
├── participant/
│   ├── signals.py      # participant_created, participant_updated
│   └── handlers.py     # side-effect + transactional handlers + register()
├── secret_friend/
│   ├── signals.py      # secret_friend_assigned
│   └── handlers.py     # side-effect handlers + register()
├── shared/
│   └── signals.py      # isolated decorator (shared infra)
└── lifecycle.py        # register_all_handlers() aggregator
```

Each domain entity owns its signals and handlers. `shared/signals.py` has only the `isolated` decorator. `lifecycle.py` aggregates all `register()` calls for `app_main.py`.

## Two Handler Categories

### 1. Side-effect handlers (`@isolated`)

Fire-and-forget. Failure is logged but **never crashes** the service. Use for logging, notifications, analytics, external API calls.

```python
from src.domain.shared.signals import isolated

@isolated
def _on_group_created(sender, *, group, **_):
    log.info("group created: %s", group.name)
    slack.notify(f"New group: {group.name}")  # if this fails, group still created
```

### 2. Transactional handlers (no decorator)

Part of the business transaction. Failure **propagates** and rolls back the transaction. Use for cross-domain state changes that must succeed.

```python
def _reveal_participant_on_assignment(sender, *, participant_id, db_session, **_):
    """Must succeed or the entire assignment rolls back."""
    ParticipantService.update(
        participant_id=participant_id,
        payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
        db_session=db_session,
    )
```

## Decision Guide

| Situation                                | Handler type     | Why                          |
| ---------------------------------------- | ---------------- | ---------------------------- |
| Logging, audit trail                     | `@isolated`      | Service doesn't depend on it |
| Email, Slack, webhook                    | `@isolated`      | External systems can fail    |
| Analytics tracking                       | `@isolated`      | Non-critical                 |
| Cross-domain state change (MUST succeed) | Transactional    | Data consistency             |
| Validation that should abort operation   | Don't use signal | Direct import                |

## Signal Emission Pattern

Services use blinker's native `signal.send()` with the service class as sender:

```python
# domain/group/service.py
from src.domain.group.signals import group_created

class GroupService:
    @staticmethod
    def create(group, db_session):
        result = GroupRepository.create(group=group, db_session=db_session)
        validated = GroupRead.model_validate(result)
        group_created.send(GroupService, group=validated)
        return validated
```

### Signal kwargs contract

Each signal documents its kwargs. Handlers use named kwargs for type safety:

```python
# Handler receives exactly what was sent — TypeError if mismatch
def handler(sender, *, group, **_):  # ← named kwarg, not .get()
```

### Passing db_session for transactional handlers

When a handler needs to participate in the same transaction, pass `db_session` through the signal:

```python
secret_friend_assigned.send(
    SecretFriendService,
    assignment=validated,
    group_id=group_id,
    participant_id=participant_id,
    db_session=db_session,  # ← same session = same transaction
)
```

## Cross-Domain Decoupling

### Before (coupled)

```python
# secret_friend/service.py imports and calls participant directly
from src.domain.participant.service import ParticipantService

class SecretFriendService:
    def assign(self, ...):
        ParticipantService.update(status=REVEALED)  # ← direct coupling
```

### After (decoupled via signal)

```python
# secret_friend/service.py emits signal — doesn't know who reacts
secret_friend_assigned.send(SecretFriendService, participant_id=id, db_session=db)

# participant/handlers.py reacts — participant owns its own state
def _reveal_on_assignment(sender, *, participant_id, db_session, **_):
    ParticipantService.update(status=REVEALED)
```

**Result:** `secret_friend` doesn't import `ParticipantUpdate` or `ParticipantStatus`. Each domain manages its own state transitions.

## Adding New Handlers

To add a new reaction (e.g., Slack notification on group creation):

1. Add handler to `domain/group/handlers.py`
2. Connect in `register()` — **never modify the service**

```python
# domain/group/handlers.py
@isolated
def _notify_slack_on_group_created(sender, *, group, **_):
    slack.post(f"New group: {group.name}")

def register():
    group_created.connect(_on_group_created)
    group_created.connect(_notify_slack_on_group_created)  # ← just add here
```

## Adding a New Domain Entity

1. Create `domain/{entity}/signals.py` with signals
2. Create `domain/{entity}/handlers.py` with handlers + `register()`
3. Add `register` import to `domain/lifecycle.py`
4. Emit signals from service

## Background Tasks (Task Relay Pattern)

The project uses a **task backend abstraction** to bridge blinker signals to background work (email, notifications, webhooks).

### Architecture

```
Service → signal.send() → relay handler → dispatch_task() → TaskBackend
                                                              ├── LoggingBackend (default, no-op)
                                                              └── CeleryBackend  (swap when ready)
```

### Files

- `domain/shared/task_backend.py` — `TaskBackend` protocol + `dispatch_task()` + `LoggingBackend`
- `domain/shared/task_relay_handlers.py` — relay handlers that bridge signals → tasks

### How relay handlers work

Relay handlers are `@isolated` handlers that call `dispatch_task()` instead of doing I/O directly:

```python
# domain/shared/task_relay_handlers.py
@isolated
def _relay_group_created(sender, *, group, **_):
    dispatch_task("notifications.group_created", group_id=group.id)
```

Today `dispatch_task()` logs the call (no-op). When Celery is added, swap the backend:

### Swapping to Celery (when ready)

```python
# 1. Install celery
# poetry add celery[redis]

# 2. Create celery_app.py
from celery import Celery
celery_app = Celery("app", broker="redis://localhost:6379/0")

# 3. Create CeleryBackend
from src.domain.shared.task_backend import TaskBackend

class CeleryBackend:
    def __init__(self, celery_app):
        self._app = celery_app

    def send(self, task_name: str, **kwargs: object) -> None:
        self._app.send_task(task_name, kwargs=kwargs)

# 4. Swap backend at startup (app_main.py)
from src.domain.shared.task_backend import set_backend
set_backend(CeleryBackend(celery_app))
```

**Zero changes** to services, signals, or relay handlers. Only the backend swap.

## Registration

All handlers are registered at app startup via `lifecycle.py`:

```python
# app_main.py
from src.domain.lifecycle import register_all_handlers

def start_application():
    create_tables()
    register_all_handlers()  # ← domain handlers + task relays
    return app
```
