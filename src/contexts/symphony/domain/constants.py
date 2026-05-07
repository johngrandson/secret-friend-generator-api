"""Symphony domain constants — pure-Python literals shared across layers.

Houses the contract-level values that the orchestrator, agents, and
adapters must agree on:

* Workspace artifact layout (the agent must write to ``.symphony/<file>``).
* Versioning floor (every aggregate version starts at 1).
* Orchestrator iteration cap (defensive against runaway pipelines).

Domain layer remains framework-free — no Pydantic, no FastAPI, no SQLAlchemy.
Use cases and adapters import from here instead of redefining literals.
"""

from typing import Final

MAX_ORCHESTRATION_ITERATIONS: Final[int] = 12

SYMPHONY_WORKSPACE_DIR: Final[str] = ".symphony"

SPEC_FILENAME: Final[str] = "spec.md"

PLAN_FILENAME: Final[str] = "plan.md"

MIN_ARTIFACT_VERSION: Final[int] = 1
