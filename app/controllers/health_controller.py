"""Liveness controller, also used by Docker to know when the API is up."""

from flask import jsonify
from sqlalchemy import text

from app.extensions import db


def health():
    """Report the API and database status."""
    try:
        db.session.execute(text("SELECT 1"))
        database = "up"
    except Exception:  # noqa: BLE001 - a health check must never raise
        database = "down"
    return jsonify({"status": "ok", "database": database})
