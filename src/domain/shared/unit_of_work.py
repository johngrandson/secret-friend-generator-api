"""UnitOfWork output port — atomic transaction boundary abstraction.

Domain services depend on this Protocol, never on SQLAlchemy. Re-entrant
implementations must let nested `atomic()` calls share the outer commit.
"""

from contextlib import AbstractContextManager
from typing import Protocol


class UnitOfWork(Protocol):
    def atomic(self) -> AbstractContextManager[None]:
        """Open an atomic block. Commits on clean exit, rolls back on raise."""
        ...
