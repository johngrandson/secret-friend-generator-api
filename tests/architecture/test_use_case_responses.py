"""Fitness function: every <Name>Response in use_cases is a @dataclass.

Use case responses are part of the Clean Architecture contract — callers
depend on a structured DTO with documented fields, not an arbitrary class.
This catches regressions where someone returns a Pydantic model, a NamedTuple,
or an anemic plain class from a use case.
"""

import ast
import dataclasses
import importlib
from collections.abc import Iterator
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
USE_CASE_PATTERNS = [
    SRC / "contexts" / "identity" / "use_cases",
    SRC / "contexts" / "symphony" / "use_cases",
    SRC / "contexts" / "tenancy" / "use_cases",
]


def _py_modules(directory: Path) -> Iterator[Path]:
    yield from (p for p in directory.rglob("*.py") if "__pycache__" not in p.parts)


def _response_class_names(tree: ast.Module) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.endswith("Response"):
            yield node.name


def _module_path_to_dotted(path: Path) -> str:
    rel = path.relative_to(SRC.parent).with_suffix("")
    return ".".join(rel.parts)


def test_use_case_responses_are_dataclass() -> None:
    """All classes ending in 'Response' under use_cases/ must be @dataclass."""
    violations: list[str] = []
    for use_case_dir in USE_CASE_PATTERNS:
        if not use_case_dir.exists():
            continue
        for path in _py_modules(use_case_dir):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            response_names = list(_response_class_names(tree))
            if not response_names:
                continue
            module_dotted = _module_path_to_dotted(path)
            try:
                module = importlib.import_module(module_dotted)
            except Exception as exc:  # noqa: BLE001
                violations.append(f"{module_dotted}: import failed ({exc})")
                continue
            for name in response_names:
                cls = getattr(module, name, None)
                if cls is None:
                    continue
                if not dataclasses.is_dataclass(cls):
                    violations.append(
                        f"{module_dotted}.{name} is not @dataclass — use case "
                        "Responses must be dataclasses (see "
                        ".claude/rules/clean-architecture-enforcement.md #10)"
                    )
    assert not violations, "Use case Response invariant violated:\n" + "\n".join(
        violations
    )
