"""Controller layer: handles the HTTP request.

A controller receives the payload already validated by the schemas, calls the
service that owns the business rule and returns the data plus the status code.
It contains no business logic and no database access.
"""

from app.controllers import (
    category_controller,
    health_controller,
    order_controller,
    product_controller,
)

__all__ = [
    "category_controller",
    "health_controller",
    "order_controller",
    "product_controller",
]
