"""Fitness function: each aggregate has exactly one repository port.

Convention: every aggregate folder under `domain/<aggregate>/` that contains
an `entity.py` must also expose a `repository.py` defining the abstract
repository (Protocol / ABC) for that aggregate. Aggregates persisted as
value objects (e.g., gate_result) follow the same convention.
"""

import ast
from collections.abc import Iterator
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
DOMAIN_GLOB = "contexts/*/domain"


def _aggregate_dirs(domain_root: Path) -> Iterator[Path]:
    """Yield direct children of a domain dir that contain entity.py or value_object.py."""
    if not domain_root.exists():
        return
    for child in domain_root.iterdir():
        if not child.is_dir() or child.name == "__pycache__":
            continue
        has_root = (child / "entity.py").exists() or (
            child / "value_object.py"
        ).exists()
        if has_root:
            yield child


def _has_repository_class(repository_file: Path) -> bool:
    """True iff repository.py defines at least one class (Protocol/ABC)."""
    if not repository_file.exists():
        return False
    tree = ast.parse(repository_file.read_text(encoding="utf-8"))
    return any(isinstance(n, ast.ClassDef) for n in ast.walk(tree))


def test_each_aggregate_has_a_repository_module() -> None:
    """domain/<aggregate>/repository.py exists and defines at least one class."""
    violations: list[str] = []
    for domain_root in SRC.glob(DOMAIN_GLOB):
        for aggregate_dir in _aggregate_dirs(domain_root):
            repo_file = aggregate_dir / "repository.py"
            if not repo_file.exists():
                violations.append(
                    f"{aggregate_dir.relative_to(SRC.parent)}: missing repository.py"
                )
                continue
            if not _has_repository_class(repo_file):
                violations.append(
                    f"{repo_file.relative_to(SRC.parent)}: defines no class — "
                    "repository.py must export a Protocol or ABC for the aggregate"
                )
    assert not violations, "Repository-per-aggregate invariant violated:\n" + "\n".join(
        violations
    )
