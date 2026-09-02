"""Category controllers: one class per resource, one method per HTTP verb."""

from flask.views import MethodView

from app.api.v1.blueprints import categories_blp as blp
from app.controllers.utils import ensure_not_empty
from app.schemas.category import (
    CategoryCreateSchema,
    CategoryListSchema,
    CategoryPatchSchema,
    CategoryQuerySchema,
    CategorySchema,
)
from app.schemas.common import ErrorSchema
from app.schemas.product import ProductListSchema, ProductQuerySchema
from app.services import category_service, product_service


class CategoryCollectionController(MethodView):
    """Endpoints of /api/v1/categories."""

    @blp.doc(tags=["Categories"], summary="List categories")
    @blp.arguments(CategoryQuerySchema, location="query")
    @blp.response(200, CategoryListSchema)
    def get(self, filters):
        """List categories with filtering, sorting and pagination."""
        return category_service.list_categories(filters)

    @blp.doc(tags=["Categories"], summary="Create a category")
    @blp.arguments(CategoryCreateSchema)
    @blp.response(201, CategorySchema)
    @blp.alt_response(409, schema=ErrorSchema, description="Name already in use")
    @blp.alt_response(422, schema=ErrorSchema, description="Validation error")
    def post(self, payload):
        """Create a new category."""
        return category_service.create_category(payload)


class CategoryController(MethodView):
    """Endpoints of /api/v1/categories/<id>."""

    @blp.doc(tags=["Categories"], summary="Retrieve a category")
    @blp.response(200, CategorySchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Category not found")
    def get(self, category_id):
        """Retrieve a single category by its identifier."""
        return category_service.get_category(category_id)

    @blp.doc(tags=["Categories"], summary="Replace a category")
    @blp.arguments(CategoryCreateSchema)
    @blp.response(200, CategorySchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Category not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Name already in use")
    def put(self, payload, category_id):
        """Full update: every writable field is replaced."""
        return category_service.replace_category(category_id, payload)

    @blp.doc(tags=["Categories"], summary="Partially update a category")
    @blp.arguments(CategoryPatchSchema)
    @blp.response(200, CategorySchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Category not found")
    @blp.alt_response(422, schema=ErrorSchema, description="Empty or invalid payload")
    def patch(self, payload, category_id):
        """Partial update: only the provided fields are changed."""
        return category_service.update_category(category_id, ensure_not_empty(payload))

    @blp.doc(tags=["Categories"], summary="Delete a category")
    @blp.response(204)
    @blp.alt_response(404, schema=ErrorSchema, description="Category not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Category still has products")
    def delete(self, category_id):
        """Delete a category that has no products associated with it."""
        category_service.delete_category(category_id)
        return ""


class CategoryProductsController(MethodView):
    """Endpoints of /api/v1/categories/<id>/products."""

    @blp.doc(tags=["Categories"], summary="List the products of a category")
    @blp.arguments(ProductQuerySchema, location="query")
    @blp.response(200, ProductListSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Category not found")
    def get(self, filters, category_id):
        """Navigate the 1:N relationship from the category side."""
        return product_service.list_products_by_category(category_id, filters)
