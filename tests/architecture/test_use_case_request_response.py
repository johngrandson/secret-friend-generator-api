"""Fitness function: every UseCase class has matching Request and Response.

Use cases follow Clean Architecture's Request/Response DTO pattern: a class
``<Name>UseCase`` is paired with ``<Name>Request`` (input) and
``<Name>Response`` (output). The DTOs may live in the same module or in a
sibling ``dtos.py`` file inside the same use-case package — both are
acceptable as they belong to the same use-case unit.
"""

import ast
from collections.abc import Iterator
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
USE_CASE_DIRS = [
    SRC / "contexts" / "identity" / "use_cases",
    SRC / "contexts" / "symphony" / "use_cases",
    SRC / "contexts" / "tenancy" / "use_cases",
]


def _py_modules(directory: Path) -> Iterator[Path]:
    yield from (p for p in directory.rglob("*.py") if "__pycache__" not in p.parts)


def _class_names(tree: ast.Module) -> set[str]:
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


def _classes_in_package(package_dir: Path) -> set[str]:
    """All classes defined in any .py file directly inside this directory."""
    names: set[str] = set()
    for path in package_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names |= _class_names(tree)
    return names


def test_use_cases_have_request_and_response() -> None:
    """For each <Name>UseCase, <Name>Request and <Name>Response exist in the same package."""
    violations: list[str] = []
    for use_case_dir in USE_CASE_DIRS:
        if not use_case_dir.exists():
            continue
        for path in _py_modules(use_case_dir):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            file_classes = _class_names(tree)
            use_case_classes = {c for c in file_classes if c.endswith("UseCase")}
            if not use_case_classes:
                continue
            package_classes = _classes_in_package(path.parent)
            for uc in use_case_classes:
                base = uc.removesuffix("UseCase")
                request_name = f"{base}Request"
                response_name = f"{base}Response"
                if request_name not in package_classes:
                    violations.append(
                        f"{path.relative_to(SRC.parent)}: {uc} has no matching "
                        f"{request_name} in package"
                    )
                if response_name not in package_classes:
                    violations.append(
                        f"{path.relative_to(SRC.parent)}: {uc} has no matching "
                        f"{response_name} in package"
                    )
    assert not violations, (
        "Use case Request/Response pairing violated:\n" + "\n".join(violations)
    )
