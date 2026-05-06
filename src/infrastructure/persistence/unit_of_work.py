"""SQLAlchemy adapter for the UnitOfWork Protocol.

Wraps the existing reentrant `transaction()` helper so domain services
never need to import SQLAlchemy.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from src.infrastructure.persistence.transaction import transaction


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def atomic(self) -> Generator[None, None, None]:
        with transaction(self._session):
            yield
