"""Marshmallow schemas: input validation and output serialization."""

from app.schemas.category import (
    CategoryCreateSchema,
    CategoryPatchSchema,
    CategoryQuerySchema,
    CategorySchema,
)
from app.schemas.common import ErrorResponseSchema, ErrorSchema, PaginationSchema
from app.schemas.order import (
    OrderCreateSchema,
    OrderItemCreateSchema,
    OrderItemPatchSchema,
    OrderItemSchema,
    OrderPatchSchema,
    OrderQuerySchema,
    OrderSchema,
    OrderUpdateSchema,
)
from app.schemas.product import (
    ProductByCategoryQuerySchema,
    ProductCreateSchema,
    ProductPatchSchema,
    ProductQuerySchema,
    ProductSchema,
    ProductSummarySchema,
)

__all__ = [
    "CategorySchema",
    "CategoryCreateSchema",
    "CategoryPatchSchema",
    "CategoryQuerySchema",
    "ProductSchema",
    "ProductCreateSchema",
    "ProductPatchSchema",
    "ProductQuerySchema",
    "OrderSchema",
    "OrderCreateSchema",
    "OrderUpdateSchema",
    "OrderPatchSchema",
    "OrderQuerySchema",
    "OrderItemSchema",
    "OrderItemCreateSchema",
    "OrderItemPatchSchema",
    "ErrorSchema",
    "ErrorResponseSchema",
    "ProductSummarySchema",
    "ProductByCategoryQuerySchema",
    "PaginationSchema",
]
