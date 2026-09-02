"""Business rules for orders and order items.

This is where the N:N relationship is managed: stock reservation, price
snapshots, allowed status transitions and total recalculation. Stock is always
moved through product_service, which owns that column.
"""

from decimal import Decimal

from app.extensions import db
from app.errors import ConflictError, ResourceNotFoundError, ValidationError
from app.models import Order, OrderItem, OrderStatus
from app.services import product_service
from app.services.pagination import apply_sorting, paginate
from app.services.transaction import transaction

# A canceled or shipped order is final; a paid order can still be shipped or canceled.
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
    OrderStatus.SHIPPED: set(),
    OrderStatus.CANCELED: set(),
}


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #
def list_orders(filters: dict) -> dict:
    """Return a paginated, filtered and sorted list of orders."""
    query = Order.query
    if (status := filters.get("status")) is not None:
        query = query.filter(Order.status == status)
    if email := filters.get("customer_email"):
        query = query.filter(Order.customer_email.ilike(f"%{email}%"))

    query = apply_sorting(query, Order, filters["sort_by"], filters["order"])
    return paginate(query, filters["page"], filters["per_page"])


def get_order(order_id: int) -> Order:
    """Return an order or raise 404."""
    order = db.session.get(Order, order_id)
    if order is None:
        raise ResourceNotFoundError(f"Order {order_id} not found")
    return order


# --------------------------------------------------------------------------- #
# Order lifecycle
# --------------------------------------------------------------------------- #
def create_order(payload: dict) -> Order:
    """Create an order, reserving stock for every requested product."""
    items = _ensure_unique_products(payload["items"])

    order = Order(
        customer_name=payload["customer_name"],
        customer_email=payload["customer_email"],
        status=OrderStatus.PENDING,
    )
    with transaction() as session:
        session.add(order)
        for entry in items:
            _reserve_and_add_line(order, entry["product_id"], entry["quantity"])
        _refresh_total(order)
    return order


def replace_order(order_id: int, payload: dict) -> Order:
    """PUT semantics: customer data and the whole item set are replaced."""
    order = get_order(order_id)
    _ensure_editable(order)
    items = _ensure_unique_products(payload["items"])

    with transaction():
        # Give the previously reserved stock back before reserving the new one.
        _release_order_stock(order)
        order.items.clear()
        db.session.flush()

        order.customer_name = payload["customer_name"]
        order.customer_email = payload["customer_email"]
        if payload.get("status") is not None:
            _change_status(order, payload["status"])

        for entry in items:
            _reserve_and_add_line(order, entry["product_id"], entry["quantity"])
        _refresh_total(order)
    return order


def update_order(order_id: int, payload: dict) -> Order:
    """PATCH semantics: partial update of customer data and/or status."""
    order = get_order(order_id)
    customer_fields = {k: v for k, v in payload.items() if k != "status"}

    with transaction():
        if "status" in payload:
            _change_status(order, payload["status"])
        if customer_fields:
            # Customer data is frozen once the order leaves the PENDING state.
            _ensure_editable(order)
            for field, value in customer_fields.items():
                setattr(order, field, value)
    return order


def delete_order(order_id: int) -> None:
    """Delete an order and return the reserved stock to the catalog."""
    order = get_order(order_id)
    with transaction() as session:
        if order.status != OrderStatus.CANCELED:
            _release_order_stock(order)
        session.delete(order)


# --------------------------------------------------------------------------- #
# Order items (the association object of the N:N relationship)
# --------------------------------------------------------------------------- #
def add_item(order_id: int, payload: dict) -> Order:
    """Add a product to a pending order."""
    order = get_order(order_id)
    _ensure_editable(order)

    product_id = payload["product_id"]
    if any(item.product_id == product_id for item in order.items):
        raise ConflictError(
            f"Product {product_id} is already in this order. "
            "Use PATCH on the item to change its quantity."
        )

    with transaction():
        _reserve_and_add_line(order, product_id, payload["quantity"])
        _refresh_total(order)
    return order


def update_item(order_id: int, item_id: int, payload: dict) -> Order:
    """Change the quantity of an item, adjusting the reserved stock."""
    order = get_order(order_id)
    _ensure_editable(order)
    item = _get_item(order, item_id)

    delta = payload["quantity"] - item.quantity
    with transaction():
        if delta > 0:
            product_service.reserve_stock(item.product, delta)
        elif delta < 0:
            product_service.release_stock(item.product, -delta)
        item.quantity = payload["quantity"]
        _refresh_total(order)
    return order


def remove_item(order_id: int, item_id: int) -> None:
    """Remove an item from a pending order and give its stock back."""
    order = get_order(order_id)
    _ensure_editable(order)
    item = _get_item(order, item_id)

    if len(order.items) == 1:
        raise ConflictError(
            "An order must contain at least one item. Delete the order instead."
        )

    with transaction():
        product_service.release_stock(item.product, item.quantity)
        order.items.remove(item)
        db.session.flush()
        _refresh_total(order)


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _reserve_and_add_line(order: Order, product_id: int, quantity: int) -> None:
    """Reserve stock and append a line with a snapshot of the current price."""
    product = product_service.get_purchasable_product(product_id)
    product_service.reserve_stock(product, quantity)
    order.items.append(
        OrderItem(product=product, quantity=quantity, unit_price=Decimal(product.price))
    )


def _release_order_stock(order: Order) -> None:
    """Return every reserved unit of the order to the catalog."""
    for item in order.items:
        product_service.release_stock(item.product, item.quantity)


def _refresh_total(order: Order) -> None:
    """The total is derived from the items and never accepted from the client."""
    db.session.flush()
    order.recalculate_total()


def _ensure_editable(order: Order) -> None:
    """Items and customer data may only change while the order is pending."""
    if not order.is_editable:
        raise ConflictError(
            f"Order {order.id} cannot be modified because its status is "
            f"'{order.status.value}'. Only PENDING orders are editable."
        )


def _change_status(order: Order, new_status: OrderStatus) -> None:
    """Validate the transition; canceling returns the units to the catalog."""
    if new_status == order.status:
        return
    if new_status not in ALLOWED_TRANSITIONS[order.status]:
        raise ConflictError(
            f"Invalid status transition: '{order.status.value}' -> '{new_status.value}'"
        )
    if new_status == OrderStatus.CANCELED:
        _release_order_stock(order)
    order.status = new_status


def _get_item(order: Order, item_id: int) -> OrderItem:
    for item in order.items:
        if item.id == item_id:
            return item
    raise ResourceNotFoundError(f"Item {item_id} not found in order {order.id}")


def _ensure_unique_products(items: list[dict]) -> list[dict]:
    """Reject payloads repeating the same product in two different lines."""
    product_ids = [entry["product_id"] for entry in items]
    duplicates = {pid for pid in product_ids if product_ids.count(pid) > 1}
    if duplicates:
        raise ValidationError(
            "Duplicated products in items",
            {"items": [f"Product(s) {sorted(duplicates)} repeated in the payload"]},
        )
    return items
