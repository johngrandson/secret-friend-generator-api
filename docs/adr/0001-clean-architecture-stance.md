# ADR-0001: Clean Architecture as default stance

- **Status:** Accepted
- **Date:** 2026-05-07
- **Deciders:** @johngrandson

## Context

The project hosts multiple bounded contexts (`identity`, `symphony`, `tenancy`)
running on FastAPI + SQLAlchemy async + Celery + dependency-injector, with an
agentic kernel under `src/shared/agentic/`. We need a layering approach that:

- Keeps domain logic free of framework concerns so it can be reasoned about and
  tested in isolation.
- Allows multiple inbound adapters (HTTP routes today, possibly Celery
  workers and CLI tomorrow) to share the same use cases.
- Allows multiple outbound adapters (SQLAlchemy now, potentially message bus
  or external HTTP services later) without rewriting use cases.
- Makes it possible to enforce these boundaries automatically — humans and
  agentic contributors should not have to remember the rules.

## Decision

We will follow **Clean Architecture** with four layers and explicit bounded
contexts:

```
src/contexts/<context>/
├── domain/        # entities, value objects, events, repository ports, UoW port
├── use_cases/     # application services orchestrating the domain
├── adapters/
│   ├── http/      # FastAPI routes (driving adapters)
│   └── persistence/  # SQLAlchemy repositories + UoW (driven adapters)
src/shared/        # cross-context abstractions (events, agentic kernel, base classes)
src/infrastructure/  # composition root: containers, database engine, Celery app
```

- We will keep dependencies pointing inward: `adapters → use_cases → domain`,
  with `shared` reachable from any layer and `infrastructure` only reachable
  from explicit DI seams.
- We will model aggregates with rich domain entities and frozen value objects
  in `domain/`, accessed via repository Protocols defined in the same layer.
- We will write use cases as classes with `Request` / `Response` dataclasses
  and an `async execute(request) -> response` method.
- We will inject all outward dependencies (UoW, repositories, event publisher,
  external clients) via the constructor, typed with Protocols.
- We will publish domain events **after** the UoW commit, never before.
- We will isolate bounded contexts: cross-context interaction goes through the
  composition root in `src/infrastructure/`, not direct imports.
- We will document the invariants in `docs/architecture.md`, the recipes in
  `docs/how-to-add-aggregate.md` and `docs/how-to-add-bounded-context.md`, and
  the agent checklist in `.claude/rules/clean-architecture-enforcement.md`.

## Alternatives considered

- **Active record / fat models** — rejected. Couples persistence and business
  logic; tests hit the database; unsuitable for multi-adapter architecture.
- **Service layer with anemic models** — rejected. Splits behaviour from data
  unnecessarily; encourages "manager" classes; loses the ability to enforce
  invariants at the entity level.
- **Hexagonal without bounded contexts** — rejected. We already have three
  distinct domains with different lifecycles (identity vs symphony vs tenancy);
  one big bag of use cases would couple them.

## Consequences

**Positive**

- Domain code is framework-free and unit-testable without infrastructure.
- New adapters (CLI, worker, gRPC) plug in without touching use cases.
- Architectural rules are enforceable by `import-linter` and pytest fitness
  functions, reducing reliance on review.
- Bounded contexts can evolve at different paces.

**Negative**

- More files per feature than a single-layer Flask/Django app.
- Newcomers need to learn the dependency rule and the request/response use case
  shape before contributing.
- Dependency injection wiring (`src/infrastructure/containers/*`) grows with
  each new use case.

**Neutral / follow-up**

- We periodically audit `.importlinter` to add new contracts as patterns emerge
  (Phase 0 done 2026-05-07; Phase 1 intra-context aggregate isolation done
  2026-05-07 with one whitelisted cross-aggregate VO reuse Organization↔Role).
- We add fitness functions to `tests/architecture/` whenever a semantic rule
  cannot be statically enforced.

## Compliance & enforcement

- Statically enforced by 14 contracts in `.importlinter`
  (`poetry run lint-imports`, blocked at pre-commit).
- Redundantly verified by AST-based fitness functions in
  `tests/architecture/test_dependency_rule.py`.
- Semantic rules (rich entities, post-commit events, aggregate boundaries)
  are reviewed against `.claude/rules/clean-architecture-enforcement.md`
  during code review.

## References

- `docs/architecture.md` — canonical layer/dependency rules
- `docs/how-to-add-aggregate.md` — recipe for new aggregates
- `docs/how-to-add-bounded-context.md` — recipe for new contexts
- `.claude/rules/clean-architecture-enforcement.md` — pre-flight checklist
- `.importlinter` — declarative contracts
- `tests/architecture/` — fitness functions
- Robert C. Martin, *Clean Architecture* (2017)
- Cosmic Python — <https://www.cosmicpython.com/book/>
