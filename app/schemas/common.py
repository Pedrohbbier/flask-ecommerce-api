"""Schemas shared across resources."""

from marshmallow import Schema, fields, validate


class ErrorResponseSchema(Schema):
    """Standard error envelope returned by every failing request."""

    error = fields.Str(required=True, metadata={"description": "Human readable message"})
    details = fields.Raw(metadata={"description": "Field level details, when available"})


# Alias used across the API layer; the class name keeps the OpenAPI component
# name unique against flask-smorest's own "Error" schema.
ErrorSchema = ErrorResponseSchema


class PaginationSchema(Schema):
    """Pagination metadata attached to every collection response."""

    page = fields.Int()
    per_page = fields.Int()
    total_items = fields.Int()
    total_pages = fields.Int()
    has_next = fields.Bool()
    has_prev = fields.Bool()


class PaginationQueryArgsSchema(Schema):
    """Query string arguments accepted by every listing endpoint."""

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    sort_by = fields.Str(load_default="id")
    order = fields.Str(load_default="asc", validate=validate.OneOf(["asc", "desc"]))


def paginated_schema(item_schema, name: str) -> type[Schema]:
    """Build a `{items: [...], pagination: {...}}` response schema."""
    return type(
        name,
        (Schema,),
        {
            "items": fields.List(fields.Nested(item_schema)),
            "pagination": fields.Nested(PaginationSchema),
        },
    )
