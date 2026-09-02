"""Version 1 of the public API."""

from app.api.v1.blueprints import BLUEPRINTS

# Importing the routes binds every URL to its controller.
from app.api.v1 import routes  # noqa: E402,F401  (import for side effects)

__all__ = ["BLUEPRINTS"]
