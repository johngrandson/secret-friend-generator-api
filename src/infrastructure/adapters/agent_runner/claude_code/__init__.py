"""Claude Code CLI adapter — implements ``IAgentRunner`` via subprocess.

Spawns the local ``claude`` CLI in subscription mode and parses its
stream-json output. Internal layout:

    args.py        — argv assembly + prompt size validation
    transport.py   — ProcessFactory Protocol + production factory
    parser.py      — stream-json parser + state aggregation
    runner.py      — orchestrates args/transport/parser into ``ClaudeCodeRunner``
    errors.py      — exception taxonomy
    mcp_config.py  — writes ``<workspace>/.mcp.json`` for the MCP-config flag
"""

from src.infrastructure.adapters.agent_runner.claude_code.args import (
    MAX_PROMPT_BYTES,
    build_args,
    validate_prompt,
)
from src.infrastructure.adapters.agent_runner.claude_code.errors import (
    ClaudeCodeBinaryNotFoundError,
    ClaudeCodeExitError,
    ClaudeCodeInputRequiredError,
    ClaudeCodePromptTooLargeError,
    ClaudeCodeResultError,
    ClaudeCodeRunnerError,
    ClaudeCodeTimeoutError,
)
from src.infrastructure.adapters.agent_runner.claude_code.mcp_config import (
    MCP_CONFIG_FILENAME,
    MCPConfigEmptyError,
    MCPConfigError,
    write_mcp_config,
)
from src.infrastructure.adapters.agent_runner.claude_code.parser import (
    EventCallback,
)
from src.infrastructure.adapters.agent_runner.claude_code.runner import (
    ClaudeCodeRunner,
)
from src.infrastructure.adapters.agent_runner.claude_code.transport import (
    ProcessFactory,
    ProcessProtocol,
    default_process_factory,
)

__all__ = [
    "MAX_PROMPT_BYTES",
    "MCP_CONFIG_FILENAME",
    "ClaudeCodeBinaryNotFoundError",
    "ClaudeCodeExitError",
    "ClaudeCodeInputRequiredError",
    "ClaudeCodePromptTooLargeError",
    "ClaudeCodeResultError",
    "ClaudeCodeRunner",
    "ClaudeCodeRunnerError",
    "ClaudeCodeTimeoutError",
    "EventCallback",
    "MCPConfigEmptyError",
    "MCPConfigError",
    "ProcessFactory",
    "ProcessProtocol",
    "build_args",
    "default_process_factory",
    "validate_prompt",
    "write_mcp_config",
]
