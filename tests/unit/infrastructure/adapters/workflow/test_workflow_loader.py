"""Unit tests for the workflow loader (YAML front matter + body parser)."""

from pathlib import Path

import pytest

from src.infrastructure.adapters.workflow import (
    WorkflowFileNotFoundError,
    WorkflowSchemaError,
    load_workflow,
)
from src.infrastructure.adapters.workflow.loader import (
    resolve_env_vars,
    split_frontmatter,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[4] / "fixtures" / "workflows" / "sample.md"
)


def test_load_workflow_parses_full_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINEAR_API_KEY", "secret-token")
    definition = load_workflow(FIXTURE_PATH)

    assert definition.config.tracker.kind == "linear"
    assert definition.config.tracker.api_key == "secret-token"
    assert definition.config.tracker.active_states == ["Todo", "In Progress"]
    assert definition.config.agent.kind == "claude_code"
    assert definition.config.harness.ci_command == "npm run ci"
    assert definition.config.mcp_servers["linear"].command == "npx"
    assert "Agent Prompt" in definition.prompt_template
    assert definition.source_path == FIXTURE_PATH.resolve()


def test_load_workflow_expands_path_relative_to_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LINEAR_API_KEY", "k")
    workflow = tmp_path / "WORKFLOW.md"
    workflow.write_text(
        """---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: foo
workspace:
  root: ./relative-root
agent:
  kind: claude_code
harness:
  ci_command: pytest
---
body
"""
    )
    definition = load_workflow(workflow)
    assert definition.config.workspace.root == (tmp_path / "relative-root").resolve()


def test_load_workflow_missing_file_raises_typed_error(tmp_path: Path) -> None:
    with pytest.raises(WorkflowFileNotFoundError):
        load_workflow(tmp_path / "missing.md")


def test_load_workflow_invalid_yaml_raises_schema_error(tmp_path: Path) -> None:
    workflow = tmp_path / "bad.md"
    workflow.write_text("---\n: : :\n---\nbody")
    with pytest.raises(WorkflowSchemaError):
        load_workflow(workflow)


def test_load_workflow_missing_required_field_raises_schema_error(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "incomplete.md"
    workflow.write_text(
        """---
tracker:
  kind: linear
  api_key: token
  project_slug: foo
workspace:
  root: /tmp/ws
agent:
  kind: claude_code
---
"""
    )
    # Missing harness — required field
    with pytest.raises(WorkflowSchemaError, match="harness"):
        load_workflow(workflow)


def test_load_workflow_unset_env_var_becomes_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("UNSET_TOKEN", raising=False)
    workflow = tmp_path / "x.md"
    workflow.write_text(
        """---
tracker:
  kind: linear
  api_key: $UNSET_TOKEN
  project_slug: foo
workspace:
  root: /tmp
agent:
  kind: claude_code
harness:
  ci_command: ci
---
"""
    )
    with pytest.raises(WorkflowSchemaError):
        load_workflow(workflow)


def test_load_workflow_no_frontmatter_returns_empty_config(tmp_path: Path) -> None:
    workflow = tmp_path / "no-fm.md"
    workflow.write_text("just a body")
    with pytest.raises(WorkflowSchemaError):
        load_workflow(workflow)


def test_split_frontmatter_handles_unclosed_delimiter() -> None:
    raw, body = split_frontmatter("---\nfoo: bar\nno closing")
    assert raw is None
    assert body == "---\nfoo: bar\nno closing"


def test_split_frontmatter_no_delimiter() -> None:
    raw, body = split_frontmatter("just markdown")
    assert raw is None
    assert body == "just markdown"


def test_split_frontmatter_extracts_block() -> None:
    raw, body = split_frontmatter("---\nkey: value\n---\nbody text")
    assert raw == "key: value"
    assert body == "body text"


def test_resolve_env_vars_walks_dicts_and_lists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FOO", "bar")
    result = resolve_env_vars(
        {"a": "$FOO", "b": ["$FOO", "literal"], "c": {"d": "$FOO"}}
    )
    assert result == {"a": "bar", "b": ["bar", "literal"], "c": {"d": "bar"}}


def test_resolve_env_vars_unset_becomes_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_VAR", raising=False)
    assert resolve_env_vars("$MISSING_VAR") is None


def test_resolve_env_vars_passthrough_non_env_strings() -> None:
    assert resolve_env_vars("just-a-value") == "just-a-value"
    assert resolve_env_vars(123) == 123
    assert resolve_env_vars(True) is True
