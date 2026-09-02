"""Product controllers."""

from flask.views import MethodView

from app.api.v1.blueprints import products_blp as blp
from app.controllers.utils import ensure_not_empty
from app.schemas.common import ErrorSchema
from app.schemas.product import (
    ProductCreateSchema,
    ProductListSchema,
    ProductPatchSchema,
    ProductQuerySchema,
    ProductSchema,
)
from app.services import product_service


class ProductCollectionController(MethodView):
    """Endpoints of /api/v1/products."""

    @blp.doc(tags=["Products"], summary="List products")
    @blp.arguments(ProductQuerySchema, location="query")
    @blp.response(200, ProductListSchema)
    def get(self, filters):
        """List products with filtering, sorting and pagination."""
        return product_service.list_products(filters)

    @blp.doc(tags=["Products"], summary="Create a product")
    @blp.arguments(ProductCreateSchema)
    @blp.response(201, ProductSchema)
    @blp.alt_response(409, schema=ErrorSchema, description="SKU already in use")
    @blp.alt_response(422, schema=ErrorSchema, description="Validation error")
    def post(self, payload):
        """Create a new product inside an existing category."""
        return product_service.create_product(payload)


class ProductController(MethodView):
    """Endpoints of /api/v1/products/<id>."""

    @blp.doc(tags=["Products"], summary="Retrieve a product")
    @blp.response(200, ProductSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Product not found")
    def get(self, product_id):
        """Retrieve a single product, including its category."""
        return product_service.get_product(product_id)

    @blp.doc(tags=["Products"], summary="Replace a product")
    @blp.arguments(ProductCreateSchema)
    @blp.response(200, ProductSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Product not found")
    @blp.alt_response(409, schema=ErrorSchema, description="SKU already in use")
    def put(self, payload, product_id):
        """Full update: every writable field is replaced."""
        return product_service.replace_product(product_id, payload)

    @blp.doc(tags=["Products"], summary="Partially update a product")
    @blp.arguments(ProductPatchSchema)
    @blp.response(200, ProductSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Product not found")
    @blp.alt_response(422, schema=ErrorSchema, description="Empty or invalid payload")
    def patch(self, payload, product_id):
        """Partial update: typical use cases are price and stock adjustments."""
        return product_service.update_product(product_id, ensure_not_empty(payload))

    @blp.doc(tags=["Products"], summary="Delete a product")
    @blp.response(204)
    @blp.alt_response(404, schema=ErrorSchema, description="Product not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Product belongs to an order")
    def delete(self, product_id):
        """Delete a product that was never ordered."""
        product_service.delete_product(product_id)
        return ""
