"""Category routes.

Prefix: /api/v1/categories
"""

from app.api.v1.blueprints import categories_blp as blp
from app.controllers.category_controller import (
    CategoryCollectionController,
    CategoryController,
    CategoryProductsController,
)

blp.route("")(CategoryCollectionController)
blp.route("/<int:category_id>")(CategoryController)
blp.route("/<int:category_id>/products")(CategoryProductsController)
