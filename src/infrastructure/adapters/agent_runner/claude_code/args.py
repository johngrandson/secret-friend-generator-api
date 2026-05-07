"""Argv assembly + prompt size validation for the Claude Code runner."""

from src.infrastructure.adapters.agent_runner.constants import MAX_PROMPT_BYTES
from src.infrastructure.adapters.agent_runner.claude_code.errors import (
    ClaudeCodePromptTooLargeError,
)
from src.infrastructure.adapters.workflow import ClaudeCodeConfig


def build_args(
    *, prompt: str, config: ClaudeCodeConfig, session_id: str | None
) -> list[str]:
    """Build the argv array for ``claude``.

    Public so tests can assert exactly what flags get passed.
    """
    args: list[str] = [
        config.command,
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        config.permission_mode,
        "--allowedTools",
        config.allowed_tools,
    ]
    if config.api_model:
        args += ["--model", config.api_model]
    if config.mcp_config_path:
        args += ["--mcp-config", config.mcp_config_path]
    if session_id:
        args += ["--resume", session_id]
    args += ["-p", prompt]
    return args


def validate_prompt(prompt: str) -> None:
    """Raise ``ClaudeCodePromptTooLargeError`` if ``prompt`` exceeds the byte cap."""
    size = len(prompt.encode("utf-8"))
    if size > MAX_PROMPT_BYTES:
        raise ClaudeCodePromptTooLargeError(
            f"Prompt is {size} bytes; max is {MAX_PROMPT_BYTES}"
        )
