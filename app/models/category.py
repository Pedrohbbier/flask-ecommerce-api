"""Category model: the "one" side of the 1:N relationship with Product."""

from app.extensions import db
from app.models.mixins import TimestampMixin


class Category(TimestampMixin, db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)

    # 1:N -> a category owns many products.
    # passive_deletes keeps the RESTRICT defined on the foreign key authoritative,
    # so the database (not only the service layer) refuses to orphan products.
    products = db.relationship(
        "Product",
        back_populates="category",
        lazy="dynamic",
        passive_deletes="all",
    )

    def __repr__(self) -> str:
        return f"<Category {self.id} {self.name}>"
