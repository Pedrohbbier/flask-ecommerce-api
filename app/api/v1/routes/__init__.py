"""URL tables of the v1 API: every module maps paths to controllers."""

from app.api.v1.routes import (
    category_routes,
    health_routes,
    order_routes,
    product_routes,
)

__all__ = ["category_routes", "health_routes", "order_routes", "product_routes"]
