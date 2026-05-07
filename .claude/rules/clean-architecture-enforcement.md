# Clean Architecture — Enforcement Rules

**Mandatory checklist for any agent (or human) before declaring an implementation
complete.** This file consolidates the invariants documented in
`docs/architecture.md`, the import-linter contracts in `.importlinter`, the
fitness functions in `tests/architecture/`, and the ADRs in `docs/adr/`.

When in doubt, read `docs/architecture.md` (source of truth) and the relevant
ADR. Do not invent rules — propose an ADR instead.

## Source-of-truth files

- `docs/architecture.md` — canonical layer/dependency rules and patterns
- `docs/how-to-add-aggregate.md` — recipe for new aggregates inside a context
- `docs/how-to-add-bounded-context.md` — recipe for new bounded contexts
- `docs/adr/` — Architectural Decision Records (decisions not statically enforceable)
- `.importlinter` — declarative dependency rules (run via `poetry run lint-imports`)
- `tests/architecture/` — pytest fitness functions (run via `pytest tests/architecture/`)
- `scripts/verify-arch.sh` — single-command pre-push validation bundle

## The 14 invariants (must hold after any change to `src/`)

### Dependency rule (enforced by `import-linter` + `tests/architecture/test_dependency_rule.py`)

1. **Domain has no framework imports.** No `fastapi`, `sqlalchemy`, `pydantic`,
   `pydantic_settings`, `dependency_injector`, `httpx`, `celery` anywhere under
   `src/contexts/*/domain/` or `src/shared/`.
2. **Use cases have no framework or adapter/infra imports.** Use cases only
   import from `domain/`, other `use_cases/`, and `shared/`. They receive
   adapters via constructor injection (Protocol typed).
3. **Adapters do not import each other.** `http/` and `persistence/` are
   independent silos; cross-talk only via the DI container at composition root.
4. **Bounded contexts do not import each other.** `identity`, `symphony`,
   `tenancy` are isolated; integration happens at the composition root in
   `src/infrastructure/`.
5. **Infrastructure imported only by HTTP DI seams.** `deps.py` and
   `orchestration_dep.py` are the designated wiring points. Persistence adapters
   may use shared base classes from `src.infrastructure.adapters.persistence.*`.
5b. **Aggregates within a context do not cross-import.** Each aggregate folder
    under `domain/<aggregate>/` is independent. Shared behaviour lives in
    domain-level helpers (`validators.py`, `constants.py`, `approval/`, etc.).
    Cross-aggregate value-object reuse (e.g., Organization referencing Role) is
    whitelisted explicitly in `.importlinter` with a comment.

### Domain modeling (enforced by review + fitness functions)

6. **Value Objects are frozen dataclasses with validation.** Every VO under
   `domain/<aggregate>/value_objects/` (or equivalent) uses
   `@dataclass(frozen=True)` and validates in `__post_init__`.
7. **Entities are rich, not anemic.** Entities expose behaviour methods, not
   only `__init__` / property getters. Enforced by
   `tests/architecture/test_rich_domain_models.py`.
8. **Aggregate Root pattern.** External code modifies the aggregate only through
   the root entity's methods. Repositories return / accept the root.
9. **Factory methods on aggregates.** Use `@classmethod create(...)` for entity
   construction with invariants. Avoid bypassing invariants by using the raw
   `__init__`.
9b. **Repository per aggregate.** Each `domain/<aggregate>/` exports a
    `repository.py` with the aggregate's repository Protocol/ABC. Enforced by
    `tests/architecture/test_repository_per_aggregate.py`.

### Use case contract (enforced by review + fitness function)

10. **Request and Response are dataclasses.** Every use case has a
    `<Name>Request` (input DTO) and `<Name>Response` (output DTO) defined as
    `@dataclass`, in the same package as the `<Name>UseCase`. The `execute()`
    method signature is
    `async def execute(self, request: <Name>Request) -> <Name>Response`.
    Enforced by `tests/architecture/test_use_case_responses.py` and
    `tests/architecture/test_use_case_request_response.py`.
11. **Domain events are published *after* the UoW commit.** The pattern is:
    ```python
    async with self._uow:
        ... # mutations
        events = aggregate.pull_events()
        await self._uow.commit()
    if events:
        await self._publisher.publish(events)
    ```
    Never publish before commit.

### Public API stability (enforced by review)

12. **Container DI provider signatures stay stable.** `src/infrastructure/containers/*.py`
    is the wiring contract. Changing an `__init__` signature of a use case
    requires updating the provider. If you cannot update the provider, do not
    change the signature.

## Pre-flight checks before declaring done

Run **all** of the following and ensure each is green:

```bash
poetry run lint-imports                    # 12 contracts kept
poetry run pytest tests/architecture/ -q   # arch fitness functions
poetry run ruff check src/                 # style + tidy imports
poetry run mypy src/                       # type check
poetry run pytest -q                       # full suite
```

Or, single command:

```bash
bash scripts/verify-arch.sh                # runs the whole bundle
```

If any of these fail and you can't make them pass, **stop**. Either:
- Fix the violation by adjusting the code (preferred), or
- Document an exception in an ADR + add a justified `ignore_imports` whitelist
  in `.importlinter` referencing the ADR.

## How to react to an import-linter violation (agent loop)

1. Read the violation message — it names `<importer> -> <imported>` and the
   broken contract.
2. Identify the category:
   - **`*-purity` broken** → wrong layer imported a framework/concrete adapter.
     Fix: inject the dependency via constructor (Protocol-typed) instead.
   - **`independence` broken** → two silos cross-imported. Fix: move the shared
     interface to a layer above (e.g., `domain/` or `shared/`), or whitelist if
     it's a legitimate DI seam.
   - **`layers` broken** → an inner layer imported an outer layer. Fix: invert
     the dependency (define a Protocol in the inner layer, implement it
     outside).
   - **`forbidden` (Phase 0) broken** → e.g., `httpx` in domain. Fix: move the
     HTTP call to an adapter, define a Protocol port in the domain.
3. Re-run `poetry run lint-imports` until kept.

## How to react to a fitness function failure

1. Read which test failed — each has a docstring naming the invariant.
2. Read the violation list emitted by the assertion message.
3. Fix the code (e.g., add `frozen=True` to a VO, add a method to an anemic
   entity, convert a Pydantic Response to `@dataclass`).
4. Re-run `pytest tests/architecture/`.

## When a rule needs an exception

Some legitimate cases break a strict reading of the rules (e.g., shared base
classes for SQLAlchemy models). For these:

1. Write an ADR in `docs/adr/<NNN>-<slug>.md` explaining the exception.
2. Add the specific `ignore_imports` to `.importlinter` with a comment linking
   to the ADR.
3. Keep the exception narrow — list specific module paths, not wildcards.

## What this file is NOT

- Not a tutorial. For step-by-step recipes, read `docs/how-to-add-aggregate.md`
  and `docs/how-to-add-bounded-context.md`.
- Not exhaustive. For full canonical rules and layer responsibilities, read
  `docs/architecture.md`.
- Not a policy doc. For decisions and rationale, read `docs/adr/`.
