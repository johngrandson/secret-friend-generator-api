"""Fitness function: domain entities are rich, not anemic.

A rich entity exposes at least one non-dunder method beyond ``__init__`` —
this includes factory classmethods (``create``), state transitions
(``set_status``, ``mark_failed``), and behaviour queries. Anemic entities
that are pure data containers should be value objects instead.
"""

import ast
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
ENTITY_GLOB = "contexts/*/domain/*/entity.py"


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _public_method_count(class_node: ast.ClassDef) -> int:
    """Methods that count as 'behaviour' — non-dunder, defined on the class."""
    count = 0
    for stmt in class_node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_dunder(stmt.name):
                count += 1
    return count


def _domain_entity_classes(tree: ast.Module) -> list[ast.ClassDef]:
    """Top-level classes in an entity.py file (skip nested helpers)."""
    return [n for n in tree.body if isinstance(n, ast.ClassDef)]


def test_domain_entities_are_not_anemic() -> None:
    """Each class in domain/*/entity.py must expose at least one behaviour method."""
    violations: list[str] = []
    for path in SRC.glob(ENTITY_GLOB):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for cls in _domain_entity_classes(tree):
            if _public_method_count(cls) == 0:
                violations.append(
                    f"{path.relative_to(SRC.parent)}: class {cls.name} is anemic — "
                    "domain entities must expose at least one behaviour method "
                    "(factory classmethod, state transition, query, etc.). "
                    "If this is just data, model it as a value object."
                )
    assert not violations, "Anemic domain entity invariant violated:\n" + "\n".join(
        violations
    )
