"""SPEC content validator — pure function, no I/O.

Verifies the four required Markdown sections are present in the generated
``.symphony/spec.md`` content. Mirrors the origem ``spec_generator``
contract so an agent run that produces malformed output fails fast at
the use-case boundary instead of polluting the aggregate.
"""

REQUIRED_SECTIONS: tuple[str, ...] = (
    "## Goals",
    "## Non-Goals",
    "## Constraints",
    "## Approach",
)


class SpecStructureError(Exception):
    """Generated SPEC content is missing one or more required sections."""


def validate_spec_content(content: str) -> None:
    """Raise ``SpecStructureError`` if any required section is missing."""
    missing = [section for section in REQUIRED_SECTIONS if section not in content]
    if missing:
        raise SpecStructureError(
            f"SPEC missing required sections: {', '.join(missing)}"
        )
