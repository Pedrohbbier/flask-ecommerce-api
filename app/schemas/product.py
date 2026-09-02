"""Product schemas."""

from marshmallow import Schema, fields, validate

from app.schemas.common import PaginationQueryArgsSchema, paginated_schema


class ProductCategorySchema(Schema):
    """Compact category representation nested inside a product."""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)


class ProductSummarySchema(Schema):
    """Compact product representation nested inside an order item."""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    sku = fields.Str(dump_only=True)


class ProductSchema(Schema):
    """Product representation returned by the API."""

    id = fields.Int(dump_only=True)
    name = fields.Str()
    sku = fields.Str()
    description = fields.Str(allow_none=True)
    price = fields.Decimal(as_string=True, places=2)
    stock = fields.Int()
    is_active = fields.Bool()
    category_id = fields.Int()
    category = fields.Nested(ProductCategorySchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ProductCreateSchema(Schema):
    """Payload for POST and PUT: full representation of the resource."""

    name = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    sku = fields.Str(required=True, validate=validate.Regexp(
        r"^[A-Za-z0-9._-]{3,32}$",
        error="SKU must be 3-32 characters long (letters, digits, '.', '_' or '-').",
    ))
    description = fields.Str(required=False, load_default=None, allow_none=True)
    price = fields.Decimal(
        required=True, places=2, as_string=True,
        validate=validate.Range(min=0.01, error="Price must be greater than zero."),
    )
    stock = fields.Int(
        required=False, load_default=0, validate=validate.Range(min=0)
    )
    is_active = fields.Bool(required=False, load_default=True)
    category_id = fields.Int(required=True, validate=validate.Range(min=1))


class ProductPatchSchema(Schema):
    """Payload for PATCH: partial update, at least one field required."""

    name = fields.Str(validate=validate.Length(min=2, max=120))
    sku = fields.Str(validate=validate.Regexp(r"^[A-Za-z0-9._-]{3,32}$"))
    description = fields.Str(allow_none=True)
    price = fields.Decimal(places=2, as_string=True, validate=validate.Range(min=0.01))
    stock = fields.Int(validate=validate.Range(min=0))
    is_active = fields.Bool()
    category_id = fields.Int(validate=validate.Range(min=1))


class ProductQuerySchema(PaginationQueryArgsSchema):
    """Filters accepted by GET /products."""

    q = fields.Str(metadata={"description": "Partial match on name or SKU"})
    category_id = fields.Int()
    min_price = fields.Decimal(places=2)
    max_price = fields.Decimal(places=2)
    is_active = fields.Bool()
    in_stock = fields.Bool(
        metadata={"description": "true: only products in stock; false: only sold out"}
    )
    sort_by = fields.Str(
        load_default="id",
        validate=validate.OneOf(["id", "name", "price", "stock", "created_at"]),
    )


ProductListSchema = paginated_schema(ProductSchema, "ProductListSchema")
