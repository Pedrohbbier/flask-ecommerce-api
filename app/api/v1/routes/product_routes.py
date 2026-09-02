"""Product routes.

Prefix: /api/v1/products
"""

from app.api.v1.blueprints import products_blp as blp
from app.controllers.product_controller import (
    ProductCollectionController,
    ProductController,
)

blp.route("")(ProductCollectionController)
blp.route("/<int:product_id>")(ProductController)
