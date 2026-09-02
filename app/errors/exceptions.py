"""Domain-level exceptions raised by the service layer.

The service layer never imports Flask: it raises these exceptions and the HTTP
layer translates them into responses (see app/errors/handlers.py).
"""

from typing import Any


class APIError(Exception):
    """Base class for every error the API knows how to answer."""

    status_code = 500
    message = "Internal server error"

    def __init__(self, message: str | None = None, details: Any = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details

    def to_dict(self) -> dict:
        payload: dict[str, Any] = {"error": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class ResourceNotFoundError(APIError):
    """404 - the requested resource or identifier does not exist."""

    status_code = 404
    message = "Resource not found"


class ValidationError(APIError):
    """422 - the payload is syntactically valid but semantically wrong."""

    status_code = 422
    message = "Validation error"


class BusinessRuleError(APIError):
    """422 - a domain rule rejected the operation (e.g. not enough stock)."""

    status_code = 422
    message = "Business rule violation"


class ConflictError(APIError):
    """409 - the operation conflicts with the current state of the resource."""

    status_code = 409
    message = "Conflict with the current state of the resource"
