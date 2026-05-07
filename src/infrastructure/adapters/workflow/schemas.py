"""Pydantic models for the WORKFLOW.md front matter."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.infrastructure.adapters.workflow.constants import (
    DEFAULT_AGENT_TIMEOUT_MS,
    DEFAULT_POLLING_INTERVAL_MS,
    DEFAULT_RETRY_CONTINUATION_MS,
    DEFAULT_RETRY_FAILURE_BASE_MS,
    DEFAULT_RETRY_JITTER_RATIO,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_RETRY_MAX_BACKOFF_MS,
    DEFAULT_STALL_TIMEOUT_MS,
    DEFAULT_TURN_TIMEOUT_MS,
)
from src.shared.agentic.retry import RetryConfig as RuntimeRetryConfig


class StrictModel(BaseModel):
    """Base for sub-section configs that must reject unknown keys."""

    model_config = ConfigDict(extra="forbid")


class TrackerConfig(StrictModel):
    """Issue tracker integration. Currently only ``linear`` is supported."""

    kind: Literal["linear", "jira"]
    api_key: str = Field(min_length=1)
    project_slug: str = Field(min_length=1)
    endpoint: str = "https://api.linear.app/graphql"
    active_states: list[str] = Field(default_factory=lambda: ["Todo", "In Progress"])
    terminal_states: list[str] = Field(
        default_factory=lambda: ["Done", "Cancelled", "Canceled", "Duplicate", "Closed"]
    )

    @field_validator("active_states", "terminal_states")
    @classmethod
    def _normalize_states(cls, value: list[str]) -> list[str]:
        return [s.strip() for s in value if s.strip()]


class PollingConfig(StrictModel):
    """How often the orchestrator polls the tracker for new work."""

    interval_ms: int = Field(default=DEFAULT_POLLING_INTERVAL_MS, ge=1_000)


class WorkspaceConfig(StrictModel):
    """Where per-issue workspaces live on the orchestrator host."""

    root: Path


class HooksConfig(StrictModel):
    """Optional shell scripts run at workspace lifecycle boundaries."""

    after_create: str | None = None
    before_run: str | None = None
    after_run: str | None = None
    before_remove: str | None = None


class AgentConfig(StrictModel):
    """High-level coding-agent configuration.

    ``mode=subscription`` spawns the local ``claude`` CLI authed with the
    operator's Pro/Max account. ``mode=api`` is reserved for future work.
    """

    kind: Literal["claude_code"]
    mode: Literal["subscription", "api"] = "subscription"
    timeout_ms: int = Field(default=DEFAULT_AGENT_TIMEOUT_MS, ge=1_000)
    max_turns: int = Field(default=20, ge=1)
    max_concurrent_agents: int = Field(default=1, ge=1)


class ClaudeCodeConfig(StrictModel):
    """Claude Code CLI invocation settings.

    The two timeouts cooperate: ``turn_timeout_ms`` is the hard wall;
    ``stall_timeout_ms`` triggers when there is no event activity for that
    long. ``stall`` must be strictly less than ``turn`` or stall detection
    never fires before the turn deadline.
    """

    command: str = Field(default="claude", min_length=1)
    api_model: str = Field(default="claude-sonnet-4-6", min_length=1)
    permission_mode: Literal["default", "acceptEdits", "bypassPermissions", "plan"] = (
        "acceptEdits"
    )
    allowed_tools: str = Field(default="Read,Edit,Write,Bash", min_length=1)
    turn_timeout_ms: int = Field(default=DEFAULT_TURN_TIMEOUT_MS, ge=1_000)
    stall_timeout_ms: int = Field(default=DEFAULT_STALL_TIMEOUT_MS, ge=0)
    mcp_config_path: str | None = None

    @model_validator(mode="after")
    def _stall_must_be_strictly_less_than_turn(self) -> "ClaudeCodeConfig":
        if self.stall_timeout_ms and self.stall_timeout_ms >= self.turn_timeout_ms:
            raise ValueError(
                f"stall_timeout_ms ({self.stall_timeout_ms}) must be strictly less "
                f"than turn_timeout_ms ({self.turn_timeout_ms}); set "
                f"stall_timeout_ms=0 to disable stall detection."
            )
        return self


class SDDConfig(StrictModel):
    """Spec-driven-development gating policy."""

    spec_required: bool = True
    plan_required: bool = True
    approval_via: Literal["cli", "linear", "both"] = "cli"


class CoverageConfig(StrictModel):
    """Coverage delta gate (blocking)."""

    enabled: bool = True
    threshold_new_lines: int = Field(default=80, ge=0, le=100)
    tool: str = "c8"


class ComplexityConfig(StrictModel):
    """Cyclomatic complexity + file LoC gate (blocking)."""

    enabled: bool = True
    max_cyclomatic: int = Field(default=15, ge=1)
    max_file_loc: int = Field(default=300, ge=1)
    tool: str = "ts-complex"


class SelfReviewConfig(StrictModel):
    """LLM self-review using a rubric (soft gate)."""

    enabled: bool = True
    rubric_path: str = ".symphony/rubric.md"


class HarnessConfig(StrictModel):
    """Quality gates that run after the agent finishes editing."""

    ci_command: str = Field(min_length=1)
    coverage: CoverageConfig = Field(default_factory=CoverageConfig)
    complexity: ComplexityConfig = Field(default_factory=ComplexityConfig)
    self_review: SelfReviewConfig = Field(default_factory=SelfReviewConfig)


class PRConfig(StrictModel):
    """How the PR is opened on GitHub once gates pass."""

    base_branch: str = Field(default="main", min_length=1)
    draft: bool = True
    labels: list[str] = Field(default_factory=lambda: ["agent-generated"])


class RetryConfigSchema(StrictModel):
    """Operator-facing retry policy for the WORKFLOW.md front matter.

    Validation-only: parses the YAML and applies bounds. The runtime
    machinery in :mod:`src.shared.agentic.retry` consumes a minimal
    :class:`RuntimeRetryConfig`; call :meth:`to_runtime` to produce one.

    Delay formula:

        attempt 1 (continuation, e.g., stall) -> continuation_delay_ms
        attempt N otherwise                   -> failure_base_ms * 2^(N-1)
                                                 ± jitter, capped at
                                                 max_backoff_ms

    ``max_attempts`` is inclusive — ``max_attempts=3`` means up to two
    retries after the initial run.
    """

    max_attempts: int = Field(default=DEFAULT_RETRY_MAX_ATTEMPTS, ge=1, le=10)
    continuation_delay_ms: int = Field(
        default=DEFAULT_RETRY_CONTINUATION_MS, ge=100
    )
    failure_base_ms: int = Field(default=DEFAULT_RETRY_FAILURE_BASE_MS, ge=100)
    max_backoff_ms: int = Field(default=DEFAULT_RETRY_MAX_BACKOFF_MS, ge=1_000)
    jitter_ratio: float = Field(
        default=DEFAULT_RETRY_JITTER_RATIO, ge=0.0, le=0.5
    )

    def to_runtime(self) -> RuntimeRetryConfig:
        """Project the operator config onto the runtime retry primitive."""
        return RuntimeRetryConfig(
            continuation_delay_ms=self.continuation_delay_ms,
            failure_base_ms=self.failure_base_ms,
            max_backoff_ms=self.max_backoff_ms,
            jitter_ratio=self.jitter_ratio,
        )


class MCPServerConfig(StrictModel):
    """One entry in the generated ``.mcp.json`` ``mcpServers`` map."""

    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    """Root config — every field of ``WORKFLOW.md`` front matter."""

    model_config = ConfigDict(extra="ignore")

    tracker: TrackerConfig
    polling: PollingConfig = Field(default_factory=PollingConfig)
    workspace: WorkspaceConfig
    hooks: HooksConfig = Field(default_factory=HooksConfig)
    agent: AgentConfig
    claude_code: ClaudeCodeConfig = Field(default_factory=ClaudeCodeConfig)
    sdd: SDDConfig = Field(default_factory=SDDConfig)
    harness: HarnessConfig
    pr: PRConfig = Field(default_factory=PRConfig)
    retry: RetryConfigSchema = Field(default_factory=RetryConfigSchema)
    # Empty map = no .mcp.json is generated; the runner falls back to whatever
    # claude_code.mcp_config_path already points at, if anything.
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Parsed WORKFLOW.md: typed config, agent-prompt body, and source path."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: WorkflowConfig
    prompt_template: str
    source_path: Path
