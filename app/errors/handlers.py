"""Global exception handlers producing standardized JSON responses."""

import logging

from flask import Flask, jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.errors.exceptions import APIError

logger = logging.getLogger(__name__)


def _json_error(message: str, status_code: int, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


def register_error_handlers(app: Flask) -> None:
    """Attach the application-wide error handlers."""

    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        return jsonify(exc.to_dict()), exc.status_code

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_error(exc: MarshmallowValidationError):
        # 422: the JSON parsed correctly but failed schema validation.
        return _json_error("Validation error", 422, exc.messages)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(exc: IntegrityError):
        # Unique constraints / foreign keys enforced by the database itself.
        logger.warning("Database integrity error: %s", exc)
        return _json_error(
            "The operation violates a database constraint "
            "(duplicated value or missing related record)",
            409,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(exc: SQLAlchemyError):
        logger.exception("Unexpected database error")
        return _json_error("Internal server error", 500)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        # Covers 400 (malformed JSON), 404 (unknown route), 405, and the
        # abort() calls issued by flask-smorest for request validation.
        details = None
        payload = getattr(exc, "data", None)
        if isinstance(payload, dict):
            details = payload.get("errors") or payload.get("messages")
            if payload.get("message") and not details:
                details = payload["message"]

        status = exc.code or 500
        # Replace the verbose default description of the schema validation error
        # raised by flask-smorest with the same wording used by our own 422s.
        message = "Validation error" if status == 422 else exc.description
        return _json_error(message, status, details)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception("Unhandled exception")
        return _json_error("Internal server error", 500)
