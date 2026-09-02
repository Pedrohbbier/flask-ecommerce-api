"""OrderItem: association object carrying the N:N Order <-> Product payload."""

from decimal import Decimal

from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Integer, nullable=False)
    # Price snapshot: keeps historical orders correct when the product price changes.
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    __table_args__ = (
        db.UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
        db.CheckConstraint("quantity >= 1", name="ck_order_items_quantity_positive"),
    )

    @property
    def subtotal(self) -> Decimal:
        return Decimal(self.unit_price) * self.quantity

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} product={self.product_id}>"
