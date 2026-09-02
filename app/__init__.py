"""Application factory."""

from flask import Flask, redirect

from app.api.v1 import BLUEPRINTS
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import api, db, migrate


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    _register_extensions(app)
    _register_blueprints(app)
    register_error_handlers(app)
    _register_cli(app)

    @app.route("/")
    def index():
        """Send visitors straight to the interactive documentation."""
        return redirect("/docs")

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    # Models must be imported before Migrate so autogenerate sees the metadata.
    from app import models  # noqa: F401

    migrate.init_app(app, db)
    api.init_app(app)


def _register_blueprints(app: Flask) -> None:
    for blueprint in BLUEPRINTS:
        api.register_blueprint(blueprint)


def _register_cli(app: Flask) -> None:
    from app.cli import register_commands

    register_commands(app)
