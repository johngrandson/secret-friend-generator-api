# DDD Patterns for Python/FastAPI: Practical Research Report

## Executive Summary

**Recommendation:** Adopt repository pattern with classical SQLAlchemy mapping + layered architecture (domain → application → infrastructure → presentation). This mirrors Elixir/Phoenix contexts while remaining Pythonic. Cosmic Python and fastapi-todo-ddd projects demonstrate production-ready patterns.

---

## Key Findings

### 1. Folder Structure (Scalable Pattern)

**Canonical structure** (per multiple open-source projects):
```
app/
├── domain/                    # Framework-agnostic business logic
│   ├── entities/             # Entity definitions (plain Python classes)
│   ├── value_objects/        # Value objects (immutable data types)
│   ├── repositories.py       # Repository interfaces (abstract base classes)
│   ├── services.py           # Domain services (pure business rules)
│   └── exceptions.py         # Domain-specific exceptions
├── application/              # Use case orchestration
│   ├── use_cases/           # Use cases (queries, commands)
│   └── services.py          # Application services coordinate layers
├── infrastructure/           # Implementation details
│   ├── repositories/        # Concrete repository implementations
│   ├── models.py            # SQLAlchemy ORM models (framework-specific)
│   └── external/            # APIs, external services
├── presentation/            # FastAPI HTTP layer
│   ├── routes/             # Route handlers
│   ├── schemas.py          # Pydantic models (request/response)
│   └── dependencies.py     # FastAPI dependency injection
└── main.py                 # Bootstrap, config
```

**Why this works:** Each layer has a single responsibility. Domain stays agnostic; infrastructure swaps without touching business logic.

---

### 2. SQLAlchemy + Domain Entity Boundary (Critical)

**Problem:** Direct ORM inheritance couples business logic to database schema.

**Solution:** Classical mapping pattern (Cosmic Python approach):
- Define domain entities as **plain Python classes** (no decorators, no ORM knowledge)
- Define SQLAlchemy models separately in infrastructure layer
- Use SQLAlchemy's `mapper()` to connect them imperatively
- Repository translates between ORM and domain models

**Benefit:** Domain code remains testable without database. Swap Postgres ↔ SQLite ↔ CSV without touching entities.

---

### 3. Repository Pattern (Over Direct ORM)

**Why repositories > direct session queries:**
- Service layer depends on abstract interface, not SQLAlchemy
- Enables easy unit testing with in-memory FakeRepository
- Swappable storage implementation (database, file, API)

**Minimal interface:**
```python
class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> None: pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> User: pass
```

**Implementation in infrastructure layer:**
```python
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session):
        self.session = session
    
    def add(self, user: User) -> None:
        orm_user = UserModel.from_domain(user)
        self.session.add(orm_user)
```

---

### 4. Service Layer (Application Logic)

**Two-tier approach:**
1. **Domain Services:** Pure business rules (no I/O, no framework knowledge)
2. **Application Services:** Orchestrate use cases, coordinate repositories, handle transactions

**Example:**
- `CreateUserUseCase` calls `user_repository.add()` → handles transaction
- Business validation happens in domain service (no duplicate emails)
- HTTP error conversion happens in presentation layer

---

### 5. Framework-Agnostic Design

**Key principle:** Domain layer imports nothing FastAPI/SQLAlchemy-specific.

**Dependency direction:** Presentation → Application → Domain ← Infrastructure
- Domain has no external dependencies
- Infrastructure and presentation depend on domain interfaces
- Application orchestrates between them

**Testability:** Domain logic tested without database mocks.

---

## Open-Source References (Production-Ready)

1. **Cosmic Python** (Harry Percival & Bob Gregory) — definitive repository pattern resource
2. **fastapi-todo-ddd** (Adam Havlicek) — complete working example with all layers
3. **python-ddd** (multiple examples) — tactical DDD patterns demonstrated
4. **NEONKID/fastapi-ddd-example** — SQLAlchemy integration patterns

---

## Trade-Offs & Adoption Notes

| Aspect | Cost | Benefit |
|--------|------|---------|
| More files/classes | Initial boilerplate | Clean boundaries, testability |
| Repository abstraction | Indirection layer | Swappable storage, mock-friendly |
| Classical mapping | Extra SQLAlchemy config | Domain remains pure Python |
| Layered architecture | Steeper learning curve | Maintainability at scale |

**Maturity:** Repository pattern + layered architecture are stable, proven patterns. FastAPI adoption of these patterns is standard across production codebases (2024+).

---

## Unresolved Questions

- How to handle cross-domain transactions (aggregates spanning multiple bounded contexts)?
- Best practices for event sourcing with FastAPI (event store vs event bus architecture)?
- Optimal use case class naming conventions (CreateUserCommand vs CreateUserUseCase)?
