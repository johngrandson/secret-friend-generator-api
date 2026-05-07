"""Fitness function: every domain event is a @dataclass(frozen=True).

Domain events are immutable records of past facts. The base class
src.shared.events.DomainEvent declares this contract; subclasses in
src/contexts/*/domain/*/events.py must respect it.
"""

import ast
import dataclasses
import importlib
from collections.abc import Iterator
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
EVENTS_FILES_GLOB = "contexts/*/domain/*/events.py"


def _module_path_to_dotted(path: Path) -> str:
    rel = path.relative_to(SRC.parent).with_suffix("")
    return ".".join(rel.parts)


def _event_class_names(tree: ast.Module) -> Iterator[str]:
    """Yield class names that look like domain events (defined in events.py)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Skip the base class itself if redefined in a subpackage.
            if node.name == "DomainEvent":
                continue
            yield node.name


def test_domain_events_are_frozen_dataclasses() -> None:
    """All event classes in domain/*/events.py must be @dataclass(frozen=True)."""
    violations: list[str] = []
    for path in SRC.glob(EVENTS_FILES_GLOB):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names = list(_event_class_names(tree))
        if not names:
            continue
        module_dotted = _module_path_to_dotted(path)
        try:
            module = importlib.import_module(module_dotted)
        except Exception as exc:  # noqa: BLE001
            violations.append(f"{module_dotted}: import failed ({exc})")
            continue
        for name in names:
            cls = getattr(module, name, None)
            if cls is None:
                continue
            if not dataclasses.is_dataclass(cls):
                violations.append(f"{module_dotted}.{name} is not @dataclass")
                continue
            params = getattr(cls, "__dataclass_params__", None)
            if params is None or not getattr(params, "frozen", False):
                violations.append(
                    f"{module_dotted}.{name} is not frozen — domain events "
                    "must be @dataclass(frozen=True) (see "
                    ".claude/rules/clean-architecture-enforcement.md #6)"
                )
    assert not violations, "Domain event immutability violated:\n" + "\n".join(
        violations
    )
