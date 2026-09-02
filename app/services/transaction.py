"""Transaction boundary used by the service layer."""

from contextlib import contextmanager

from app.extensions import db


@contextmanager
def transaction():
    """Commit the staged work, rolling back if any rule rejects the operation.

    Every write in a service runs inside this block, so a use case is atomic:
    if the second item of an order has no stock, the units reserved for the
    first one are never persisted.
    """
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
