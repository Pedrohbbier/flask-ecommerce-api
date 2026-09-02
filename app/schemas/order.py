"""Order and order item schemas."""

from marshmallow import Schema, fields, validate

from app.models.order import OrderStatus
from app.schemas.common import PaginationQueryArgsSchema, paginated_schema
from app.schemas.product import ProductSummarySchema


class OrderItemSchema(Schema):
    """Order line returned by the API."""

    id = fields.Int(dump_only=True)
    product_id = fields.Int(dump_only=True)
    quantity = fields.Int(dump_only=True)
    unit_price = fields.Decimal(as_string=True, places=2, dump_only=True)
    subtotal = fields.Decimal(as_string=True, places=2, dump_only=True)
    product = fields.Nested(ProductSummarySchema, dump_only=True)


class OrderItemCreateSchema(Schema):
    """Payload used to add a line to an order."""

    product_id = fields.Int(required=True, validate=validate.Range(min=1))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class OrderItemPatchSchema(Schema):
    """Payload used to change the quantity of an existing line."""

    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class OrderSchema(Schema):
    """Order representation returned by the API."""

    id = fields.Int(dump_only=True)
    customer_name = fields.Str()
    customer_email = fields.Email()
    status = fields.Enum(OrderStatus, by_value=True)
    total_amount = fields.Decimal(as_string=True, places=2, dump_only=True)
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class OrderCreateSchema(Schema):
    """Payload for POST /orders. The total is always computed server-side."""

    customer_name = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    customer_email = fields.Email(required=True)
    items = fields.List(
        fields.Nested(OrderItemCreateSchema),
        required=True,
        validate=validate.Length(min=1, error="An order must contain at least one item."),
    )


class OrderUpdateSchema(OrderCreateSchema):
    """Payload for PUT /orders/<id>: replaces customer data and the whole item set."""

    status = fields.Enum(OrderStatus, by_value=True, load_default=None)


class OrderPatchSchema(Schema):
    """Payload for PATCH /orders/<id>: partial update, items untouched."""

    customer_name = fields.Str(validate=validate.Length(min=2, max=120))
    customer_email = fields.Email()
    status = fields.Enum(OrderStatus, by_value=True)


class OrderQuerySchema(PaginationQueryArgsSchema):
    """Filters accepted by GET /orders."""

    status = fields.Enum(OrderStatus, by_value=True)
    customer_email = fields.Str()
    sort_by = fields.Str(
        load_default="id",
        validate=validate.OneOf(["id", "total_amount", "status", "created_at"]),
    )


OrderListSchema = paginated_schema(OrderSchema, "OrderListSchema")
