"""Category schemas."""

from marshmallow import Schema, fields, validate

from app.schemas.common import PaginationQueryArgsSchema, paginated_schema


class CategorySchema(Schema):
    """Category representation returned by the API."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    description = fields.Str(allow_none=True, validate=validate.Length(max=255))
    product_count = fields.Method("get_product_count", dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_product_count(self, obj) -> int:
        return obj.products.count()


class CategoryCreateSchema(Schema):
    """Payload for POST and PUT: every writable field is required."""

    name = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    description = fields.Str(
        required=False, load_default=None, allow_none=True,
        validate=validate.Length(max=255),
    )


class CategoryPatchSchema(Schema):
    """Payload for PATCH: every field is optional, but at least one is required."""

    name = fields.Str(validate=validate.Length(min=2, max=80))
    description = fields.Str(allow_none=True, validate=validate.Length(max=255))


class CategoryQuerySchema(PaginationQueryArgsSchema):
    """Filters accepted by GET /categories."""

    name = fields.Str(metadata={"description": "Case-insensitive partial match"})
    sort_by = fields.Str(
        load_default="id", validate=validate.OneOf(["id", "name", "created_at"])
    )


CategoryListSchema = paginated_schema(CategorySchema, "CategoryListSchema")
