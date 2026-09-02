"""Health routes."""

from app.api.v1.blueprints import health_blp as blp
from app.controllers import health_controller

blp.route("/health", methods=["GET"])(health_controller.health)
