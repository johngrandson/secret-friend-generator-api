"""AST-based layer purity checks — zero external dependencies.

Redundant safety net for import-linter: catches violations when someone
runs only `pytest` without `lint-imports`.
"""

import ast
from pathlib import Path
from typing import Iterator

SRC = Path(__file__).parents[2] / "src"

_DOMAIN_FORBIDDEN = {
    "fastapi",
    "sqlalchemy",
    "pydantic",
    "pydantic_settings",
    "dependency_injector",
    "httpx",
    "src.use_cases",
    "src.adapters",
    "src.infrastructure",
}

_USE_CASES_FORBIDDEN = {
    "fastapi",
    "sqlalchemy",
    "pydantic",
    "pydantic_settings",
    "dependency_injector",
    "httpx",
    "src.adapters",
    "src.infrastructure",
}


def _py_files(directory: Path) -> Iterator[Path]:
    yield from directory.rglob("*.py")


def _import_names(tree: ast.Module) -> Iterator[tuple[int, str]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.lineno, node.module


def _check_layer(layer_dir: Path, forbidden: set[str]) -> list[str]:
    violations: list[str] = []
    for path in _py_files(layer_dir):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno, module in _import_names(tree):
            for forbidden_prefix in forbidden:
                if module == forbidden_prefix or module.startswith(forbidden_prefix + "."):
                    violations.append(
                        f"{path.relative_to(SRC.parent)}:{lineno}: "
                        f"forbidden import '{module}' (matches '{forbidden_prefix}')"
                    )
                    break
    return violations


def test_domain_layer_is_pure() -> None:
    """src/domain/ must not import any framework or outer layer."""
    violations = _check_layer(SRC / "domain", _DOMAIN_FORBIDDEN)
    assert not violations, (
        "Domain layer purity violated:\n" + "\n".join(violations)
    )


def test_use_cases_layer_is_pure() -> None:
    """src/use_cases/ must not import frameworks, adapters, or infrastructure."""
    violations = _check_layer(SRC / "use_cases", _USE_CASES_FORBIDDEN)
    assert not violations, (
        "Use cases layer purity violated:\n" + "\n".join(violations)
    )
