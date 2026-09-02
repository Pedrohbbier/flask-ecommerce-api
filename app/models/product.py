"""Product model: N:1 with Category and N:N with Order through OrderItem."""

from app.extensions import db
from app.models.mixins import TimestampMixin


class Product(TimestampMixin, db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    sku = db.Column(db.String(32), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    category = db.relationship("Category", back_populates="products")
    order_items = db.relationship(
        "OrderItem",
        back_populates="product",
        passive_deletes="all",
    )

    __table_args__ = (
        db.CheckConstraint("price > 0", name="ck_products_price_positive"),
        db.CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.id} {self.sku}>"
