"""Root conftest.py — pre-imports app_main with create_tables patched to a no-op.

app_main.py calls create_tables() at module level which connects to Postgres.
By patching Base.metadata.create_all before the first import we keep the test
session entirely in SQLite (managed by tests/conftest.py fixtures).
"""
import sys
from unittest.mock import patch

import src.infrastructure.database.base  # ensure module is imported before patch resolves


def _preload_app_main():
    """Import app_main exactly once with create_tables suppressed."""
    if "src.app_main" in sys.modules:
        return
    # Patch the method that would open a Postgres connection at module load time.
    with patch("src.infrastructure.database.base.Base.metadata.create_all"):
        import src.app_main  # noqa: F401


_preload_app_main()
