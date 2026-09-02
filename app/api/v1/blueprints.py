"""Blueprint instances of the v1 API.

They live in their own module so that controllers can use the OpenAPI
decorators and route files can register the URLs, without a circular import.
"""

from flask_smorest import Blueprint

health_blp = Blueprint(
    "health", __name__, url_prefix="/api/v1", description="Service health"
)
categories_blp = Blueprint(
    "categories",
    __name__,
    url_prefix="/api/v1/categories",
    description="CRUD for product categories",
)
products_blp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/v1/products",
    description="CRUD for catalog products",
)
orders_blp = Blueprint(
    "orders",
    __name__,
    url_prefix="/api/v1/orders",
    description="CRUD for customer orders",
)

BLUEPRINTS = (health_blp, categories_blp, products_blp, orders_blp)
