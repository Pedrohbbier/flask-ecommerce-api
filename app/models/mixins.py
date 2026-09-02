"""Reusable model mixins."""

from datetime import datetime, timezone

from app.extensions import db


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adds automatic created_at / updated_at columns."""

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
