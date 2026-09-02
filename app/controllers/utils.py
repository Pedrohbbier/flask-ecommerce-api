"""Helpers shared by the controllers."""

from app.errors import ValidationError


def ensure_not_empty(payload: dict) -> dict:
    """A PATCH with an empty body has nothing to apply -> 422."""
    if not payload:
        raise ValidationError("Empty payload: provide at least one field to update")
    return payload
