"""shared/agentic — kernel agentic primitives (Protocols + pure utilities).

This package is the boundary for genuinely-generic agentic primitives:
workspace lifecycle, gate execution, agent runner contracts, retry policy.
Implementations (claude_code, filesystem workspace, CIGate) live in
``src/infrastructure/adapters/`` or ``src/contexts/<vertical>/adapters/``.

Hard rules (enforced via import-linter contract ``shared-agentic-purity``):

- Zero Pydantic
- Zero SQLAlchemy
- Zero ``src.contexts.*`` imports
- Zero ``src.infrastructure.*`` imports
- Stdlib + ``src.shared.*`` only

If you reach for one of those, you are leaking infra/domain knowledge into
the kernel and the contract will fail. Re-think where the abstraction belongs.
"""

from src.shared.agentic.agent_runner import (
    IAgentRunner,
    TokenUsage,
    TurnResult,
)
from src.shared.agentic.gate import (
    Gate,
    GateName,
    GateOutcome,
    GateRunner,
    GateStatus,
)
from src.shared.agentic.retry import (
    AgentTerminalError,
    AgentTransientStallError,
    RetryConfig,
    RetryKind,
    classify_failure,
    compute_delay,
)
from src.shared.agentic.workspace import (
    HookResult,
    IWorkspaceManager,
    Workspace,
)

__all__ = [
    "AgentTerminalError",
    "AgentTransientStallError",
    "Gate",
    "GateName",
    "GateOutcome",
    "GateRunner",
    "GateStatus",
    "HookResult",
    "IAgentRunner",
    "IWorkspaceManager",
    "RetryConfig",
    "RetryKind",
    "TokenUsage",
    "TurnResult",
    "Workspace",
    "classify_failure",
    "compute_delay",
]
