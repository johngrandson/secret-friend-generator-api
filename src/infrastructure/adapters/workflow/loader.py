"""WORKFLOW.md loader — YAML front matter + agent prompt body.

Reads a Markdown file with optional YAML front matter and produces a fully
typed ``WorkflowDefinition``. The loader is the only place that knows about
file IO, YAML, env var resolution, and path expansion — every downstream
consumer receives validated typed objects.

Resolution order:
    1. Read file as UTF-8.
    2. Split front matter (between leading ``---`` and the next ``---``) from body.
    3. Parse front matter as YAML. Empty / missing front matter -> empty config.
    4. Resolve ``$VAR_NAME`` strings against ``os.environ`` recursively.
    5. Expand ``~`` and resolve relative path-shaped fields against the
       WORKFLOW.md directory.
    6. Validate via Pydantic.
    7. Wrap with the trimmed Markdown body as ``prompt_template``.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from src.infrastructure.adapters.workflow.constants import (
    ENV_VAR_PATTERN,
    FRONT_MATTER_DELIMITER,
)
from src.infrastructure.adapters.workflow.schemas import (
    WorkflowConfig,
    WorkflowDefinition,
)

log = logging.getLogger(__name__)

# Dotted paths whose string values are filesystem paths and get ``~`` expansion +
# relative-to-WORKFLOW.md resolution.
PATH_FIELDS = ("workspace.root",)


class WorkflowLoaderError(Exception):
    """Base error for any failure in the workflow loader."""


class WorkflowFileNotFoundError(WorkflowLoaderError):
    """Raised when the WORKFLOW.md file does not exist or is unreadable."""


class WorkflowSchemaError(WorkflowLoaderError):
    """Raised when the YAML front matter is malformed or fails validation."""


def load_workflow(path: Path | str) -> WorkflowDefinition:
    """Parse a WORKFLOW.md and return a typed ``WorkflowDefinition``.

    Raises:
        WorkflowFileNotFoundError: file does not exist or cannot be read.
        WorkflowSchemaError: front matter is non-map YAML, unparseable, or
            fails Pydantic validation.
    """
    source_path = Path(path).resolve()
    try:
        content = source_path.read_text(encoding="utf-8")
    except FileNotFoundError as err:
        log.warning("WORKFLOW.md not found: %s", source_path)
        raise WorkflowFileNotFoundError(
            f"WORKFLOW.md not found: {source_path}"
        ) from err
    except OSError as err:
        log.warning("WORKFLOW.md unreadable at %s: %s", source_path, err)
        raise WorkflowFileNotFoundError(
            f"WORKFLOW.md unreadable at {source_path}: {err}"
        ) from err

    raw_config, prompt_template = split_frontmatter(content)
    config_dict = _parse_yaml(raw_config, source_path) if raw_config else {}
    config_dict = resolve_env_vars(config_dict)
    config_dict = _expand_paths(config_dict, base_dir=source_path.parent)

    try:
        config = WorkflowConfig.model_validate(config_dict)
    except ValidationError as err:
        message = _format_schema_error(err, source_path)
        log.warning("Invalid WORKFLOW.md schema: %s", message)
        raise WorkflowSchemaError(message) from err

    return WorkflowDefinition(
        config=config,
        prompt_template=prompt_template.strip(),
        source_path=source_path,
    )


def split_frontmatter(content: str) -> tuple[str | None, str]:
    """Split a Markdown document into ``(front_matter, body)``.

    A document opens with front matter when the first line is exactly ``---``.
    Everything between the opening ``---`` and the next standalone ``---`` is
    the front matter; the rest is the body. If no front matter exists or the
    opening delimiter is unclosed, returns ``(None, content)``.
    """
    if not content.startswith(FRONT_MATTER_DELIMITER):
        return None, content

    lines = content.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONT_MATTER_DELIMITER:
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])

    return None, content


def resolve_env_vars(value: Any) -> Any:
    """Recursively replace ``$VAR_NAME`` strings with ``os.environ[VAR_NAME]``.

    A string matching ``^\\$[A-Z_][A-Z0-9_]*$`` is treated as a reference.
    Unset / empty env vars become ``None`` so missing-required-field
    validation surfaces a precise schema error.
    """
    if isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_env_vars(item) for item in value]
    if isinstance(value, str):
        match = ENV_VAR_PATTERN.match(value)
        if not match:
            return value
        resolved = os.environ.get(match.group(1), "")
        return resolved or None
    return value


def _parse_yaml(raw: str, source_path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(raw)
    except yaml.YAMLError as err:
        raise WorkflowSchemaError(
            f"Front matter is not valid YAML at {source_path}: {err}"
        ) from err

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise WorkflowSchemaError(
            f"Front matter must decode to a map at {source_path}, "
            f"got {type(loaded).__name__}"
        )
    return loaded


def _expand_paths(config: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Expand ``~`` and resolve relative path-shaped fields against ``base_dir``."""
    for dotted_path in PATH_FIELDS:
        keys = dotted_path.split(".")
        cursor: Any = config
        for key in keys[:-1]:
            if not isinstance(cursor, dict) or key not in cursor:
                cursor = None
                break
            cursor = cursor[key]
        if isinstance(cursor, dict) and isinstance(cursor.get(keys[-1]), str):
            cursor[keys[-1]] = _expand_path(cursor[keys[-1]], base_dir)
    return config


def _expand_path(raw: str, base_dir: Path) -> Path:
    path = Path(os.path.expanduser(raw))
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve(strict=False)


def _format_schema_error(err: ValidationError, source_path: Path) -> str:
    errors = err.errors()
    if not errors:
        return f"Invalid WORKFLOW.md schema at {source_path}: {err}"
    first = errors[0]
    location = ".".join(str(part) for part in first["loc"]) or "<root>"
    return f"Invalid WORKFLOW.md at {source_path}: field '{location}' — {first['msg']}"
