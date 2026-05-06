# Python AI Starter — Clean Architecture

A production-ready Python starter using strict Clean Architecture / Hexagonal / DDD
with **vertical-slicing per bounded context**, Unit of Work, and domain events.
The canonical bounded contexts are `identity` (User CRUD) and `symphony` (Run/Spec/Plan),
demonstrating how to extend the pattern to any new domain.

## Architecture

```
+----------------------------------------------+
|  Infrastructure  (FastAPI, SQLAlchemy, DI)   |  <- outer
+----------------------------------------------+
|  Adapters        (HTTP routes, Persistence)  |
+----------------------------------------------+
|  Use Cases       (Application orchestration) |
+----------------------------------------------+
|  Domain          (Entities, Value Objects)   |  <- inner / pure Python
+----------------------------------------------+
```

**Dependency rule**: inner layers never import from outer layers.
`src/contexts/*/domain/` has zero imports from `fastapi`, `sqlalchemy`, `pydantic`,
or any framework. Enforced automatically by `poetry run lint-imports` (CI: `test-arch`).

Full layer guide: [`docs/architecture.md`](docs/architecture.md).

## Stack

| Concern | Library |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| DB driver (prod) | asyncpg (PostgreSQL) |
| DB driver (test) | aiosqlite (SQLite in-memory) |
| Migrations | Alembic (async engine) |
| Dependency injection | dependency-injector — Container per bounded context, sessions per-request via FastAPI `Depends`, transactions via UoW |
| Settings | pydantic-settings |
| Testing | pytest + pytest-asyncio + httpx |
| Lint / format | ruff |
| Type checking | mypy |
| Architecture enforcement | import-linter (`poetry run lint-imports`) — 7 contracts |

## Project structure

```
src/
├── main.py                              # FastAPI factory + lifespan
├── shared/                             # Cross-context primitives (pure Python)
│   ├── aggregate_root.py               # AggregateRoot (collect_event / pull_events)
│   ├── events.py                       # DomainEvent base dataclass
│   └── event_publisher.py             # IEventPublisher Protocol (output port)
├── infrastructure/
│   ├── config.py                       # pydantic-settings Settings
│   ├── database.py                     # get_session (per-request) + init_db
│   ├── containers/{core,identity,symphony,root}.py  # DI containers
│   └── adapters/
│       ├── events/in_memory_publisher.py
│       └── persistence/{base,registry}.py
└── contexts/
    ├── identity/                        # Bounded Context: user identity
    │   ├── domain/{unit_of_work,user/{entity,email,events,repository}}.py
    │   ├── use_cases/user/{dto,create,get,list,update,delete}.py
    │   └── adapters/
    │       ├── http/user/{router,schemas,serializers,deps,routes/*}.py
    │       └── persistence/{unit_of_work,user/{model,mapper,repository}}.py
    └── symphony/                        # Bounded Context: runs, specs, plans
        ├── domain/{unit_of_work,run/*,spec/*,plan/*,backlog/*}.py
        ├── use_cases/{run,spec,plan}/*.py
        └── adapters/
            ├── http/{run,spec,plan,backlog}/__init__.py  # placeholders
            └── persistence/{unit_of_work,run/*,spec/*,plan/*}.py

tests/
├── conftest.py                          # SQLite engine, Fake UoW, FakePublisher fixtures
├── architecture/test_dependency_rule.py # AST layer purity checks
├── unit/
│   ├── domain/user/{test_email,test_entity}.py
│   └── use_cases/{identity,symphony}/  # use case unit tests with Fake UoW
└── integration/
    ├── identity/{test_repository,test_endpoints,test_event_publication}.py
    └── symphony/
```

## Local setup

### Prerequisites

- Python 3.11+
- Poetry
- Docker (for PostgreSQL)

### Steps

```bash
# 1. Install dependencies
poetry install

# 2. Configure environment
cp .env.example .env
# Edit DATABASE_URL if needed (default: postgresql+asyncpg://postgres:postgres@localhost:5432/app)

# 3. Start PostgreSQL
docker compose -f docker/docker-compose.yml up -d postgres

# 4. Run migrations
poetry run alembic upgrade head

# 5. Start the server
poetry run start
# API available at http://localhost:8000/docs
```

## API endpoints

Only `identity` HTTP routes are wired. Symphony aggregates (Run, Spec, Plan) have
domain, use-case, and persistence layers implemented — HTTP routes are placeholders
awaiting wiring.

| Method | Path | Description |
|---|---|---|
| POST | `/users/` | Create user (201) |
| GET | `/users/` | List users (paginated: limit/offset) |
| GET | `/users/{id}` | Get user by id (404 if missing) |
| PATCH | `/users/{id}` | Update name / is_active (404 if missing) |
| DELETE | `/users/{id}` | Delete user (204 / 404 if missing) |

## Running tests

```bash
# All tests — unit + integration against SQLite in-memory (no Postgres required)
poetry run pytest -q

# With coverage
poetry run pytest --cov=src --cov-report=term-missing
```

## Lint, type checking, and architecture enforcement

```bash
poetry run ruff check src tests
poetry run mypy src

# Architecture enforcement (layer boundary contracts — 7 contracts)
poetry run lint-imports
```

## How to extend

- **Add an aggregate inside an existing context** → [`docs/how-to-add-aggregate.md`](docs/how-to-add-aggregate.md)
- **Add a new bounded context** → [`docs/how-to-add-bounded-context.md`](docs/how-to-add-bounded-context.md)
