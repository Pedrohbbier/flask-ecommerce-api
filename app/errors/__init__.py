"""Domain exceptions and global error handling."""

from app.errors.exceptions import (
    APIError,
    BusinessRuleError,
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.errors.handlers import register_error_handlers

__all__ = [
    "APIError",
    "BusinessRuleError",
    "ConflictError",
    "ResourceNotFoundError",
    "ValidationError",
    "register_error_handlers",
]
