# ADR-NNNN: <Title — short, imperative>

- **Status:** Proposed | Accepted | Superseded by ADR-MMMM | Deprecated
- **Date:** YYYY-MM-DD
- **Deciders:** @user (driver), @reviewer1, @reviewer2

## Context

What problem are we solving? What forces are at play (technical, organisational,
constraints, deadlines)? Why is this decision needed *now*? Keep it factual —
the goal is to let a future reader judge whether the rationale still holds.

## Decision

The decision in one paragraph. Imperative voice: "We will …". Be specific
enough that a reader can implement against it without re-deriving the choice.

If the decision has multiple parts, list them as a bullet list of imperative
statements:

- We will …
- We will not …
- The boundary case X is handled by …

## Alternatives considered

Briefly list the options that were rejected and why. One bullet per option:

- **Option A — <name>** — rejected because <reason>.
- **Option B — <name>** — rejected because <reason>.

## Consequences

What becomes easier? What becomes harder? What follow-up work does this
unlock or require? Be honest about the trade-offs.

- **Positive:** …
- **Negative:** …
- **Neutral / follow-up:** …

## Compliance & enforcement

How is this decision kept honest over time? Pick the strongest mechanism that
applies:

- Statically enforced by `<contract>` in `.importlinter`.
- Verified by `tests/architecture/<test_file>.py`.
- Not statically enforceable; relies on review against this ADR.

## References

- Related ADRs: ADR-MMMM
- Related code: `path/to/file.py`
- External: <link to article, RFC, blog post>
