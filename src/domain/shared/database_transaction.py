from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(db_session: Session) -> Generator[Session, None, None]:
    """Atomic operation wrapper. Repos must use flush(), not commit().
    Services call this for multi-step operations that need atomicity.
    Do not nest — each service method should be the single transaction boundary."""
    try:
        yield db_session
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
