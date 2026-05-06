"""Root conftest — set ENV=test before any import."""

import os

os.environ.setdefault("ENV", "test")
