"""Canonical exception types raised by the run-pipeline use cases.

Each use case used to declare its own ``InvalidRunStateForXError`` and
``*FileMissingError``. The classes themselves are short — the duplication
was the import cycle they would create once ``status_guards.py`` and
``artifact_io.py`` need to raise them.

This module is the single source of truth. The original use case modules
re-export their respective exceptions to preserve the public import path
for existing tests.
"""


class InvalidRunStateError(Exception):
    """``ExecuteRun`` was invoked while ``Run.status`` was unexpected."""


class InvalidRunStateForPRError(Exception):
    """``OpenPR`` was invoked while ``Run.status`` was unexpected."""


class InvalidRunStateForGatesError(Exception):
    """``RunGates`` was invoked while ``Run.status`` was unexpected."""


class MissingArtifactError(Exception):
    """A required spec or plan artifact was absent at gate time."""


class SpecFileMissingError(Exception):
    """Agent finished but did not write ``<workspace>/.symphony/spec.md``."""


class PlanFileMissingError(Exception):
    """Agent finished but did not write ``<workspace>/.symphony/plan.md``."""
