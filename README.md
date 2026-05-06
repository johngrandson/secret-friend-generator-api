# Python AI Starter — Clean Architecture

A production-ready Python starter using strict Clean Architecture / Hexagonal / DDD patterns.
The canonical domain example is a **User** aggregate with full CRUD, demonstrating how to add
any new domain object to the same layered structure.

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
`src/domain/` has zero imports from `fastapi`, `sqlalchemy`, `pydantic`, or any framework.

- **Architecture rules**: see [`docs/architecture.md`](docs/architecture.md) for the full
  layer boundary guide. Rules are enforced automatically by `poetry run lint-imports`
  (CI: job `test-arch`).

## Stack

| Concern | Library |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| DB driver (prod) | asyncpg (PostgreSQL) |
| DB driver (test) | aiosqlite (SQLite in-memory) |
| Migrations | Alembic (async engine) |
| Dependency injection | dependency-injector — `Container` owns engine/session-factory/use-case factories; sessions stay per-request via FastAPI `Depends(get_session)` |
| Settings | pydantic-settings |
| Testing | pytest + pytest-asyncio + httpx |
| Lint / format | ruff |
| Type checking | mypy |
| Architecture enforcement | import-linter (`poetry run lint-imports`) |

## Project structure

```
src/
├── main.py                                      # FastAPI factory + lifespan
├── domain/user/
│   ├── entity.py                                # User aggregate root (dataclass)
│   ├── email.py                                 # Email value object (frozen dataclass)
│   └── repository.py                            # IUserRepository (Protocol — output port)
├── use_cases/user/
│   ├── create.py
│   ├── get.py
│   ├── list.py
│   ├── update.py
│   └── delete.py
├── adapters/
│   ├── http/user/
│   │   ├── _router.py                           # APIRouter definition
│   │   ├── schemas.py                           # Pydantic input schemas
│   │   ├── serializers.py                       # entity → dict
│   │   ├── deps.py                              # FastAPI Depends wiring
│   │   └── routes/{create,get,list,update,delete}.py
│   └── persistence/user/
│       ├── model.py                             # SQLAlchemy UserModel
│       ├── mapper.py                            # entity ↔ model conversion
│       └── repository.py                        # SQLAlchemyUserRepository
└── infrastructure/
    ├── config.py                                # pydantic-settings Settings
    ├── container.py                             # DI Container (engine, session factory, use cases)
    └── database.py                              # get_session (per-request) + init_db

tests/
├── conftest.py                                  # SQLite engine + client fixtures
├── architecture/
│   └── test_dependency_rule.py                  # AST-based layer purity checks
├── unit/
│   ├── domain/user/{test_email,test_entity}.py
│   └── use_cases/user/test_{create,get,list,update,delete}.py
└── integration/user/
    ├── test_repository.py                       # repo against SQLite
    └── test_endpoints.py                        # full HTTP via httpx AsyncClient
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

## Lint and type checking

```bash
poetry run ruff check src tests
poetry run mypy src

# Architecture enforcement (layer boundary contracts)
poetry run lint-imports
```

## How to add a new aggregate

See [`docs/how-to-add-aggregate.md`](docs/how-to-add-aggregate.md) for a complete
end-to-end walkthrough (domain → use cases → persistence adapter → HTTP adapter →
container wiring → tests).
