"""Order controllers, including the nested items (N:N with products)."""

from flask.views import MethodView

from app.api.v1.blueprints import orders_blp as blp
from app.controllers.utils import ensure_not_empty
from app.schemas.common import ErrorSchema
from app.schemas.order import (
    OrderCreateSchema,
    OrderItemCreateSchema,
    OrderItemPatchSchema,
    OrderListSchema,
    OrderPatchSchema,
    OrderQuerySchema,
    OrderSchema,
    OrderUpdateSchema,
)
from app.services import order_service


class OrderCollectionController(MethodView):
    """Endpoints of /api/v1/orders."""

    @blp.doc(tags=["Orders"], summary="List orders")
    @blp.arguments(OrderQuerySchema, location="query")
    @blp.response(200, OrderListSchema)
    def get(self, filters):
        """List orders with filtering, sorting and pagination."""
        return order_service.list_orders(filters)

    @blp.doc(tags=["Orders"], summary="Create an order")
    @blp.arguments(OrderCreateSchema)
    @blp.response(201, OrderSchema)
    @blp.alt_response(422, schema=ErrorSchema, description="Invalid product or stock")
    def post(self, payload):
        """Create an order, reserving stock and snapshotting the prices."""
        return order_service.create_order(payload)


class OrderController(MethodView):
    """Endpoints of /api/v1/orders/<id>."""

    @blp.doc(tags=["Orders"], summary="Retrieve an order")
    @blp.response(200, OrderSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Order not found")
    def get(self, order_id):
        """Retrieve an order with all of its items."""
        return order_service.get_order(order_id)

    @blp.doc(tags=["Orders"], summary="Replace an order")
    @blp.arguments(OrderUpdateSchema)
    @blp.response(200, OrderSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Order not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Order is not editable")
    @blp.alt_response(422, schema=ErrorSchema, description="Invalid product or stock")
    def put(self, payload, order_id):
        """Full update: customer data and the entire item set are replaced."""
        return order_service.replace_order(order_id, payload)

    @blp.doc(tags=["Orders"], summary="Partially update an order")
    @blp.arguments(OrderPatchSchema)
    @blp.response(200, OrderSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Order not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Invalid status transition")
    def patch(self, payload, order_id):
        """Partial update, typically a status transition (PENDING -> PAID)."""
        return order_service.update_order(order_id, ensure_not_empty(payload))

    @blp.doc(tags=["Orders"], summary="Delete an order")
    @blp.response(204)
    @blp.alt_response(404, schema=ErrorSchema, description="Order not found")
    def delete(self, order_id):
        """Delete an order and return its reserved stock to the catalog."""
        order_service.delete_order(order_id)
        return ""


class OrderItemCollectionController(MethodView):
    """Endpoints of /api/v1/orders/<id>/items."""

    @blp.doc(tags=["Orders"], summary="Add an item to an order")
    @blp.arguments(OrderItemCreateSchema)
    @blp.response(201, OrderSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Order not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Order not editable or duplicated product")
    @blp.alt_response(422, schema=ErrorSchema, description="Invalid product or stock")
    def post(self, payload, order_id):
        """Attach a product to a pending order."""
        return order_service.add_item(order_id, payload)


class OrderItemController(MethodView):
    """Endpoints of /api/v1/orders/<id>/items/<item_id>."""

    @blp.doc(tags=["Orders"], summary="Update the quantity of an item")
    @blp.arguments(OrderItemPatchSchema)
    @blp.response(200, OrderSchema)
    @blp.alt_response(404, schema=ErrorSchema, description="Order or item not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Order is not editable")
    @blp.alt_response(422, schema=ErrorSchema, description="Insufficient stock")
    def patch(self, payload, order_id, item_id):
        """Change the quantity of an item, adjusting the reserved stock."""
        return order_service.update_item(order_id, item_id, ensure_not_empty(payload))

    @blp.doc(tags=["Orders"], summary="Remove an item from an order")
    @blp.response(204)
    @blp.alt_response(404, schema=ErrorSchema, description="Order or item not found")
    @blp.alt_response(409, schema=ErrorSchema, description="Order is not editable")
    def delete(self, order_id, item_id):
        """Detach a product from a pending order."""
        order_service.remove_item(order_id, item_id)
        return ""
