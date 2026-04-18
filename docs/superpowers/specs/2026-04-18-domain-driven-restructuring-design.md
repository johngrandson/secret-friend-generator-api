# Domain-Driven Restructuring Design

**Date:** 2026-04-18
**Status:** Approved
**Inspired by:** Skaffold (Elixir/Phoenix) — `/home/joao/CodeHorizon/skaffold`

## Goal

Restructure the Python starter project from a flat `src/app/` layout into a 3-layer domain-driven architecture with explicit naming, inspired by Skaffold's Phoenix contexts pattern.

## Layer Mapping

| Skaffold (Elixir) | Python | Responsibility |
|---|---|---|
| `lib/skaffold/` | `src/domain/` | Business logic, models, repos, schemas |
| `lib/skaffold_api/` | `src/api/` | REST endpoints, HTTP error mapping |
| `lib/skaffold_web/` | `src/web/` | Future (templates, SSR) |
| shared | `src/shared/` | Config, utils, cross-cutting |

## Dependency Flow

```
shared <-- domain <-- api
                  <-- web (future)
```

- `api/` imports from `domain/` — never the reverse
- `domain/` imports from `shared/` — never from `api/`
- `domain/` contexts can import from each other (e.g., participant imports group model)

## Target Structure

```
src/
  app_main.py                        # FastAPI init, middleware, mount
  domain/                            # Business logic layer
    __init__.py
    group/
      __init__.py
      group_model.py
      group_schemas.py
      group_service.py
      group_repository.py
    participant/
      __init__.py
      participant_model.py
      participant_schemas.py
      participant_service.py
      participant_repository.py
    secret_friend/
      __init__.py
      secret_friend_model.py
      secret_friend_schemas.py
      secret_friend_service.py
      secret_friend_repository.py
    shared/                          # Domain infrastructure (DB, exceptions, transactions)
      __init__.py
      database_base.py
      database_session.py
      database_transaction.py
      domain_exceptions.py
      domain_validators.py
  api/                               # REST API layer
    __init__.py
    api_router.py
    api_dependencies.py              # Shared deps (get_db, common helpers)
    api_error_schemas.py
    api_middleware.py
    auth/                            # Auth context (future: accounts domain)
      __init__.py
      auth_dependencies.py           # get_current_user, require_authenticated
    group/
      __init__.py
      group_routes.py
    participant/
      __init__.py
      participant_routes.py
    secret_friend/
      __init__.py
      secret_friend_routes.py
  web/                               # Future web layer
    __init__.py
  shared/                            # App-level config and utilities (consumed by any layer)
    __init__.py
    app_config.py
    rate_limiter_config.py
    scheduler_config.py
    instance_manager.py              # Dynamic class loader (moved from common/managers.py)
    utils/
      __init__.py
      hashing_utils.py

bin/
  run.py

tests/
  conftest.py
  domain/
    group/
    participant/
    secret_friend/
  api/
    group/
    participant/
    secret_friend/
```

## Code Patterns (Reference: Participant)

### Pattern 1: Schemas (source of truth for enums and DTOs)

File: `src/domain/{context}/{context}_schemas.py`

- Enums defined here, imported by model
- `Create` schema: no `id`, no `from_attributes`, only client-writable fields
- `Read` schema: `from_attributes = True`, all fields including `id` and FKs, no defaults on DB-generated fields
- `Update` schema: all Optional, `@model_validator` with `@classmethod` to enforce at-least-one
- `List` schema: wraps `list[Read]` for future pagination

### Pattern 2: Model (SQLAlchemy 2.0)

File: `src/domain/{context}/{context}_model.py`

- Uses `Mapped[T]` + `mapped_column()` (SA 2.0 style)
- Imports enums from schemas (single source of truth)
- `datetime.now(timezone.utc)` for all timestamps via lambdas
- Relationships typed as `Mapped[Optional["RelatedModel"]]`

### Pattern 3: Repository (data access)

File: `src/domain/{context}/{context}_repository.py`

- `@staticmethod` methods, receives `Session` as parameter
- Uses `select()` + `db_session.execute()` (SA 2.0 style, not `session.query()`)
- Raises `NotFoundError` for missing entities
- Raises `ConflictError` for `IntegrityError`
- Returns ORM model instances (not schemas)

### Pattern 4: Service (business logic orchestration)

File: `src/domain/{context}/{context}_service.py`

- `@staticmethod` methods, receives `Session` as parameter
- Calls repository, converts ORM results to Pydantic schemas via `model_validate()`
- Returns schema instances (not ORM models)
- Domain exceptions propagate through (not caught here)

### Pattern 5: Routes (HTTP adapter)

File: `src/api/{context}/{context}_routes.py`

- Thin adapter: receive request -> call service -> return response
- Zero business logic
- Catches `NotFoundError` -> 404, `ConflictError` -> 409
- No generic `except Exception` (middleware handles unexpected errors)
- Uses `response_model` for OpenAPI docs
- Imports schemas from domain, never defines own schemas

### Pattern 6: Domain Exceptions

File: `src/domain/shared/domain_exceptions.py`

- `NotFoundError(Exception)` — entity not found
- `ConflictError(Exception)` — integrity/uniqueness violation

### Pattern 7: Middleware (api layer)

File: `src/api/api_middleware.py`

- `ExceptionMiddleware` — catches unhandled exceptions, returns 500
- `MetricsMiddleware` — logs elapsed time per request
- Security headers middleware

### Pattern 8: Dependencies as Plugs (inspired by Phoenix pipelines)

Files: `src/api/api_dependencies.py` (shared) + `src/api/{context}/{context}_dependencies.py` (per-context)

Phoenix uses **plugs** chained in **pipelines** to build request context incrementally.
In FastAPI, the equivalent is **`Depends()` chaining** — each dependency resolves its
upstream dependencies automatically, and raises `HTTPException` to halt (like `conn |> halt()`).

**File organization (mirrors Skaffold's plug placement):**

- `src/api/api_dependencies.py` — shared deps used across contexts (get_db)
- `src/api/auth/auth_dependencies.py` — auth plugs (get_current_user, require_authenticated)
- `src/api/orgs/orgs_dependencies.py` — org plugs (get_current_org, get_membership, require_admin)
- `src/api/billing/billing_dependencies.py` — billing plugs (require_active_subscription)

Each API context owns its dependencies alongside its routes, just like Skaffold keeps
plugs colocated with their controllers (`controllers/orgs/org_plugs.ex`).

**Mapping:**

| Phoenix Plug | FastAPI Dependency | Purpose |
|---|---|---|
| `plug :fetch_current_user` | `Depends(get_current_user)` | Auth token -> User |
| `plug :assign_org_data` | `Depends(get_current_org)` | org_slug -> Org (validated) |
| `plug :require_org_member` | `Depends(get_current_membership)` | User + Org -> Membership |
| `plug :require_org_admin` | `Depends(require_org_admin)` | Membership.role == admin |
| `plug :subscribed_entity_only` | `Depends(require_active_subscription)` | Billing gate |
| `conn.assigns` | Function parameters (injected) | Request-scoped state |
| `conn \|> halt()` | `raise HTTPException(...)` | Abort request chain |
| `pipeline :authenticated` | `dependencies=[...]` on APIRouter | Router-level composition |
| `assign_new` (lazy eval) | FastAPI resolves each Depends once per request | Built-in caching |

**Dependency chain (mirrors Skaffold's pipeline composition):**

```
get_db
  -> get_current_user(token -> User)
       -> get_current_org(org_slug -> Org)
            -> get_current_membership(User + Org -> Membership)
                 -> require_org_admin(Membership.role == admin)
```

**Implementation rules:**

- Each dependency does ONE thing (single responsibility, like a plug)
- Dependencies raise `HTTPException` to halt — never return None for required values
- Downstream dependencies declare upstream as `Depends()` parameters — FastAPI resolves the chain
- Dependencies live in `src/api/api_dependencies.py` (api layer, not domain)
- Dependencies call domain services — never query the DB directly
- Router-level `dependencies=[...]` applies to all routes in a group (like `pipe_through`)

**Reference implementation:**

```python
# src/api/auth/auth_dependencies.py
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from src.domain.shared.database_session import get_db


def get_current_user(
    request: Request, db_session: Session = Depends(get_db)
) -> "User":
    """Plug equivalent: :fetch_current_user"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    from src.domain.accounts.accounts_service import AccountsService
    user = AccountsService.get_user_by_token(token=token, db_session=db_session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return user
```

```python
# src/api/orgs/orgs_dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.domain.shared.database_session import get_db
from src.api.auth.auth_dependencies import get_current_user


def get_current_org(
    org_slug: str,  # injected from route path param — only use on routes with {org_slug}
    current_user: "User" = Depends(get_current_user),
    db_session: Session = Depends(get_db),
) -> "Org":
    """Plug equivalent: :assign_org_data"""
    from src.domain.orgs.orgs_service import OrgsService
    org = OrgsService.get_org_by_slug(slug=org_slug, db_session=db_session)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return org


def get_current_membership(
    current_user: "User" = Depends(get_current_user),
    current_org: "Org" = Depends(get_current_org),
    db_session: Session = Depends(get_db),
) -> "Membership":
    """Plug equivalent: :require_org_member"""
    from src.domain.orgs.orgs_service import OrgsService
    membership = OrgsService.get_membership(
        user_id=current_user.id, org_id=current_org.id, db_session=db_session
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    return membership


def require_org_admin(
    membership: "Membership" = Depends(get_current_membership),
) -> "Membership":
    """Plug equivalent: :require_org_admin"""
    if membership.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return membership
```

**Usage in routes (composable like Phoenix pipelines):**

```python
# Any member can list
@router.get("/org/{org_slug}/members")
def list_members(
    membership: Membership = Depends(get_current_membership),
    db_session: Session = Depends(get_db),
):
    return OrgsService.list_members(org_id=membership.org_id, db_session=db_session)


# Admin only
@router.delete("/org/{org_slug}/members/{member_id}")
def remove_member(
    member_id: int,
    membership: Membership = Depends(require_org_admin),
    db_session: Session = Depends(get_db),
):
    return OrgsService.remove_member(
        org_id=membership.org_id, member_id=member_id, db_session=db_session
    )


# Router-level dependency (like pipeline :authenticated)
authenticated_router = APIRouter(
    prefix="/app",
    dependencies=[Depends(get_current_user)],
)
```

**Note:** The accounts and orgs domain contexts do not exist yet in this project.
This pattern documents HOW to implement them when needed, following the established
architecture. The current migration scope covers only the existing entities
(group, participant, secret_friend).

### Pattern 9: Composed Transactions (inspired by Ecto.Multi)

File: `src/domain/shared/database_transaction.py`

Ecto.Multi composes multiple DB operations into a single atomic transaction.
In SQLAlchemy, a context manager achieves the same. Repos MUST use `flush()`
instead of `commit()` when called inside a transaction — the wrapper manages commit/rollback.

```python
from contextlib import contextmanager
from sqlalchemy.orm import Session


@contextmanager
def transaction(db_session: Session):
    """Atomic operation wrapper. Repos must use flush(), not commit().
    Services call this for multi-step operations that need atomicity.
    Do not nest — each service method should be the single transaction boundary."""
    try:
        yield db_session
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
```

**Repo adjustment required:** repositories must call `db_session.flush()` (writes to DB
without committing) instead of `db_session.commit()`. The transaction wrapper or the
route-level code manages the final commit. This allows repos to be composed atomically.

**Usage in service:**

```python
def create_group_with_participants(payload, db_session: Session) -> GroupRead:
    with transaction(db_session):
        group = GroupRepository.create(payload.group, db_session)
        for p in payload.participants:
            ParticipantRepository.create(
                ParticipantCreate(name=p.name, group_id=group.id), db_session
            )
    return GroupRead.model_validate(group)
```

### Pattern 10: Reusable Domain Validators (inspired by ChangesetExt)

File: `src/domain/shared/domain_validators.py`

Skaffold's `ChangesetExt` provides `validate_email`, `validate_url`, `ensure_trimmed`
as composable validators across schemas. In Python, plain functions that raise ValueError
are used inside Pydantic `@field_validator` decorators.

```python
import re


def validate_email(value: str) -> str:
    """Reusable email validator. Use inside @field_validator."""
    value = value.strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
        raise ValueError("Invalid email address")
    if len(value) > 160:
        raise ValueError("Email must be 160 characters or less")
    return value


def validate_url(value: str) -> str:
    """Validates and normalizes URL. Prepends https:// if scheme absent."""
    value = value.strip()
    if not value:
        raise ValueError("URL cannot be blank")
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    if not re.match(r"https?://[^\s/$.?#].[^\s]*", value):
        raise ValueError("Invalid URL")
    return value


def validate_not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Field cannot be blank")
    return value
```

**Usage in Pydantic schema:**

```python
from pydantic import field_validator
from src.domain.shared.domain_validators import validate_email

class UserCreate(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email(v)
```

### Pattern 11: Testing Fixtures (inspired by Skaffold fixtures)

File: `tests/conftest.py`

Skaffold uses fixture modules (`AccountsFixtures`, `OrgsFixtures`) to create test entities
with sensible defaults and composable overrides. In Python, pytest fixtures with factory
functions achieve the same.

```python
# Imports for fixtures (domain imports omitted for brevity — add per entity)
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.domain.shared.database_base import Base

TEST_DATABASE_URL = "sqlite:///:memory:"  # or postgres test DB via env var


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """Each test runs in a transaction that is rolled back on teardown."""
    connection = engine.connect()
    txn = connection.begin()
    session = Session(connection)  # positional arg, not bind= (removed in SA 2.0)
    yield session
    session.close()
    txn.rollback()
    connection.close()


@pytest.fixture
def group_fixture(db_session: Session):
    def _create(**overrides):
        defaults = {"name": "Test Group", "description": "A test group"}
        return GroupRepository.create(
            GroupCreate(**{**defaults, **overrides}), db_session
        )
    return _create


@pytest.fixture
def participant_fixture(db_session: Session, group_fixture):
    def _create(group=None, **overrides):
        group = group or group_fixture()
        defaults = {"name": "Test Participant", "group_id": group.id}
        return ParticipantRepository.create(
            ParticipantCreate(**{**defaults, **overrides}), db_session
        )
    return _create
```

## Migration from Current Structure

### Files to Move

| Current Path | New Path |
|---|---|
| `src/app/main.py` | `src/app_main.py` |
| `src/app/api.py` | `src/api/api_router.py` |
| `src/app/config.py` | `src/shared/app_config.py` |
| `src/app/dependencies.py` | `src/api/api_dependencies.py` |
| `src/app/exceptions.py` | `src/domain/shared/domain_exceptions.py` |
| `src/app/rate_limiter.py` | `src/shared/rate_limiter_config.py` |
| `src/app/scheduler.py` | `src/shared/scheduler_config.py` |
| `src/app/database/base_class.py` | `src/domain/shared/database_base.py` |
| `src/app/database/session.py` | `src/domain/shared/database_session.py` |
| `src/app/common/utils/hashing.py` | `src/shared/utils/hashing_utils.py` |
| `src/app/common/utils/config.py` | Merged into `src/shared/app_config.py` (single config source) |
| `src/app/common/managers.py` | `src/shared/instance_manager.py` |
| `src/app/group/model.py` | `src/domain/group/group_model.py` |
| `src/app/group/schema.py` | `src/domain/group/group_schemas.py` |
| `src/app/group/service.py` | `src/domain/group/group_service.py` |
| `src/app/group/repository.py` | `src/domain/group/group_repository.py` |
| `src/app/group/views.py` | `src/api/group/group_routes.py` |
| `src/app/participant/*` | `src/domain/participant/` + `src/api/participant/` |
| `src/app/secret_friend/*` | `src/domain/secret_friend/` + `src/api/secret_friend/` |

### Code Upgrades During Migration

1. **SQLAlchemy 2.0**: `Column` -> `Mapped` + `mapped_column`, `session.query()` -> `select()`
2. **Pydantic v2**: `Config` class -> `model_config` dict, add `@classmethod` to validators
3. **Timezone-aware**: `datetime.now` -> `datetime.now(timezone.utc)`
4. **Enum consolidation**: single definition in schemas, imported by models
5. **Exception hierarchy**: `ValueError` -> `NotFoundError` / `ConflictError`. Audit all existing 8 exception classes in `src/app/exceptions.py` and all `except` blocks in views before removing old classes
6. **Import paths**: all absolute from `src.`
7. **Repo commit strategy**: `commit()` -> `flush()` in repos, commit managed by transaction wrapper or route
8. **Domain validators**: create shared validators module for reuse across schemas
9. **Test fixtures**: implement pytest fixtures with factory pattern and transaction rollback

### Files to Delete After Migration

- `src/app/` (entire directory — all contents moved)

### External References to Update

- `bin/run.py` — update import from `src.app.main:app` to `src.app_main:app`
- `alembic/env.py` — update `Base` import path
- `pyproject.toml` — update entry point if defined
- `docker/Dockerfile` — update CMD if hardcoded

## Constraints

- No new dependencies required
- Alembic migrations remain in `alembic/` (unchanged)
- Database schema unchanged (no migration needed)
- All existing API endpoints preserved (same URLs, same behavior)
- Tests must pass after restructuring

## Success Criteria

- All imports use absolute paths from `src.`
- No circular imports between layers
- `api/` never imports ORM models directly — routes only import from `{ctx}_schemas.py` and `{ctx}_service.py`
- All timestamps are timezone-aware (UTC)
- All SA models use `Mapped` + `mapped_column`
- All repos use `select()` instead of `session.query()`
- All repos use `flush()` instead of `commit()` (transaction wrapper manages commit)
- Domain exceptions used instead of `ValueError`
- Domain validators module exists with reusable validators
- Test fixtures use factory pattern with transaction rollback
- `bin/run.py` starts the app successfully
- Existing tests pass (with updated imports)
