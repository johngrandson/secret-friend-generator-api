"""Root conftest.py — pre-imports app_main with create_tables patched to a no-op.

app_main.py calls create_tables() at module level which connects to Postgres.
By patching Base.metadata.create_all before the first import we keep the test
session entirely in SQLite (managed by tests/conftest.py fixtures).

Sets ENV=test so CeleryBackend is not activated during tests.
"""
import os
import sys
from unittest.mock import patch

os.environ.setdefault("ENV", "test")

import src.infrastructure.persistence.base  # noqa: E402 — ensure module is imported before patch resolves


def _preload_app_main():
    """Import app_main exactly once with create_tables suppressed."""
    if "src.app_main" in sys.modules:
        return
    with patch("src.infrastructure.persistence.base.Base.metadata.create_all"):
        import src.app_main  # noqa: F401


_preload_app_main()
