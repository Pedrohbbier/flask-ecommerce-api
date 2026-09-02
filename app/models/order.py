"""Order model: the "many" side of the N:N relationship with Product."""

import enum
from decimal import Decimal

from app.extensions import db
from app.models.mixins import TimestampMixin


class OrderStatus(str, enum.Enum):
    """Lifecycle of an order. Only PENDING orders may be edited."""

    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class Order(TimestampMixin, db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False, index=True)
    status = db.Column(
        db.Enum(OrderStatus, native_enum=False, length=20),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    # Association object: deleting an order removes its items (cascade), but never
    # the products themselves.
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_editable(self) -> bool:
        """Items and customer data may only change while the order is pending."""
        return self.status == OrderStatus.PENDING

    def recalculate_total(self) -> Decimal:
        """Recompute the total from the items. The client never sends a total."""
        self.total_amount = sum(
            (item.subtotal for item in self.items), Decimal("0.00")
        )
        return self.total_amount

    def __repr__(self) -> str:
        return f"<Order {self.id} {self.status}>"
