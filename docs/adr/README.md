# Architectural Decision Records

Significant architectural choices that cannot be enforced statically (by
`import-linter`, `mypy`, or fitness functions in `tests/architecture/`) live
here. Each ADR captures the context, decision, and consequences so future
contributors understand *why* the codebase looks the way it does.

## Index

| ID | Title | Status |
|----|-------|--------|
| [0001](0001-clean-architecture-stance.md) | Clean Architecture as default stance | Accepted |

## Conventions

- File names: `NNNN-kebab-slug.md` (4-digit zero-padded ID).
- Format: short-form MADR (see `0000-template.md`).
- Status values: `Proposed` | `Accepted` | `Superseded by NNNN` | `Deprecated`.
- Once accepted, an ADR is **immutable** in spirit — corrections are fine, but
  to change a decision, write a new ADR that supersedes it. Update the old ADR's
  status to `Superseded by NNNN`.

## When to write an ADR

Write an ADR when the decision is:

- **Architectural** (affects layer boundaries, bounded contexts, persistence
  approach, eventing, etc.).
- **Hard to reverse** (database choice, framework choice, public API contract).
- **Not enforceable by tooling** (e.g., "rich domain models", "events published
  post-commit pattern", "aggregate boundaries").

Skip the ADR for code-style choices, bug fixes, or anything covered by an
existing ADR.

## How to write one

1. Copy `0000-template.md` to `NNNN-your-decision-slug.md`.
2. Fill in: Context, Decision, Consequences. Keep it short — one page is
   ideal, two pages maximum.
3. Set status to `Proposed`, open a PR, discuss, then flip to `Accepted` on
   merge.
4. Add a row to the index above.
