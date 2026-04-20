from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(db_session: Session) -> Generator[Session, None, None]:
    """Atomic operation wrapper. Repos must use flush(), not commit().

    Re-entrant: if already inside a transaction (detected via session.info),
    yields without committing — the outermost transaction owns the commit.
    This allows services to call other services without nested commit issues.
    """
    if db_session.info.get("_in_transaction"):
        # Already inside a transaction — just yield, don't commit/rollback
        yield db_session
        return

    db_session.info["_in_transaction"] = True
    try:
        yield db_session
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
    finally:
        db_session.info.pop("_in_transaction", None)
