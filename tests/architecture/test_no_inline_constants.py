"""AST-based anti-regression sweep for the symphony Tidy refactor.

The Tidy phases (T01–T03) extracted magic strings, magic numbers and
regex patterns into dedicated ``constants.py`` modules. This test fails
when a literal escapes back into a non-allowlisted module — early signal
that someone re-introduced an inline magic value.

Strategy: parse each ``src/**/*.py`` file with :mod:`ast`, walk all
``Constant`` nodes (which excludes ``# comments`` naturally and excludes
the module-level docstring via :func:`ast.get_docstring`), and check
whether the constant value matches a forbidden literal. Each forbidden
literal carries an explicit allowlist of files where it is allowed to
appear (the constants modules themselves).
"""

import ast
from collections.abc import Iterator
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"


# (literal_value, allowlisted_relative_paths) —
# every other .py file in `src/` must NOT contain this literal.
_FORBIDDEN_STRING_LITERALS: tuple[tuple[str, frozenset[str]], ...] = (
    (
        ".symphony",
        frozenset({"contexts/symphony/domain/constants.py"}),
    ),
    (
        "spec.md",
        frozenset(
            {
                "contexts/symphony/domain/constants.py",
                # Allowed: prompt template path constant
                "contexts/symphony/use_cases/spec/generate.py",
            }
        ),
    ),
    (
        "plan.md",
        frozenset(
            {
                "contexts/symphony/domain/constants.py",
                "contexts/symphony/use_cases/plan/generate.py",
            }
        ),
    ),
)


_FORBIDDEN_NUMERIC_LITERALS: tuple[tuple[int, frozenset[str]], ...] = (
    (
        100_000,
        frozenset({"infrastructure/adapters/agent_runner/constants.py"}),
    ),
    (
        1_800_000,
        frozenset({"infrastructure/adapters/workflow/constants.py"}),
    ),
    (
        1_000_000,
        frozenset({"infrastructure/adapters/workspace/constants.py"}),
    ),
    (
        # Orchestrator iteration cap — should live in domain/constants only.
        12,
        frozenset(
            {
                "contexts/symphony/domain/constants.py",
                # Allowed: PR API timing knobs unrelated to orchestration cap.
                "contexts/symphony/adapters/code_host/github/adapter.py",
                "infrastructure/adapters/workflow/schemas.py",
            }
        ),
    ),
)


def _py_files() -> Iterator[Path]:
    yield from SRC.rglob("*.py")


def _module_docstring_node(tree: ast.Module) -> ast.AST | None:
    """Return the AST node holding the module's docstring (or ``None``)."""
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        return tree.body[0].value
    return None


def _constants(tree: ast.Module) -> Iterator[tuple[int, object]]:
    """Yield ``(lineno, value)`` for every non-docstring Constant node."""
    docstring = _module_docstring_node(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or node is docstring:
            continue
        # Skip docstrings inside functions/classes too — they are an
        # ``Expr.Constant`` directly inside the body.
        yield node.lineno, node.value


def _relpath(path: Path) -> str:
    return path.relative_to(SRC).as_posix()


def test_no_inline_dot_symphony_string() -> None:
    """``.symphony`` must only appear in ``domain/constants.py``."""
    violations: list[str] = []
    for path in _py_files():
        rel = _relpath(path)
        for literal, allowlist in _FORBIDDEN_STRING_LITERALS:
            if rel in allowlist:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for lineno, value in _constants(tree):
                if isinstance(value, str) and value == literal:
                    violations.append(f"{rel}:{lineno}: inline literal {literal!r}")
    assert not violations, (
        "Magic-string regression — extract to a constants module:\n"
        + "\n".join(violations)
    )


def test_no_inline_magic_numeric_literals() -> None:
    """Numeric magic values must live in their constants module."""
    violations: list[str] = []
    for path in _py_files():
        rel = _relpath(path)
        for literal, allowlist in _FORBIDDEN_NUMERIC_LITERALS:
            if rel in allowlist:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for lineno, value in _constants(tree):
                # ``value is True / False`` are also ints in Python — exclude.
                if isinstance(value, bool):
                    continue
                if isinstance(value, int) and value == literal:
                    violations.append(f"{rel}:{lineno}: inline literal {literal!r}")
    assert not violations, (
        "Magic-number regression — extract to a constants module:\n"
        + "\n".join(violations)
    )
