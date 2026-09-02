"""Business rules for products, including the stock primitives."""

from app.extensions import db
from app.errors import BusinessRuleError, ConflictError, ResourceNotFoundError, ValidationError
from app.models import Category, OrderItem, Product
from app.services.pagination import apply_sorting, paginate
from app.services.transaction import transaction


def list_products(filters: dict) -> dict:
    """Return a paginated, filtered and sorted list of products."""
    query = Product.query
    if term := filters.get("q"):
        pattern = f"%{term}%"
        query = query.filter(
            db.or_(Product.name.ilike(pattern), Product.sku.ilike(pattern))
        )
    if (category_id := filters.get("category_id")) is not None:
        query = query.filter(Product.category_id == category_id)
    if (min_price := filters.get("min_price")) is not None:
        query = query.filter(Product.price >= min_price)
    if (max_price := filters.get("max_price")) is not None:
        query = query.filter(Product.price <= max_price)
    if (is_active := filters.get("is_active")) is not None:
        query = query.filter(Product.is_active.is_(is_active))
    if filters.get("in_stock"):
        query = query.filter(Product.stock > 0)

    query = apply_sorting(query, Product, filters["sort_by"], filters["order"])
    return paginate(query, filters["page"], filters["per_page"])


def list_products_by_category(category_id: int, filters: dict) -> dict:
    """Products of a single category. Raises 404 if the category is unknown."""
    if db.session.get(Category, category_id) is None:
        raise ResourceNotFoundError(f"Category {category_id} not found")
    return list_products({**filters, "category_id": category_id})


def get_product(product_id: int) -> Product:
    """Return a product or raise 404."""
    product = db.session.get(Product, product_id)
    if product is None:
        raise ResourceNotFoundError(f"Product {product_id} not found")
    return product


def create_product(payload: dict) -> Product:
    """Create a product after validating the SKU and the referenced category."""
    _ensure_unique_sku(payload["sku"])
    _ensure_category_exists(payload["category_id"])
    product = Product(**payload)
    with transaction() as session:
        session.add(product)
    return product


def replace_product(product_id: int, payload: dict) -> Product:
    """PUT semantics: every writable field is overwritten."""
    product = get_product(product_id)
    _ensure_unique_sku(payload["sku"], exclude_id=product_id)
    _ensure_category_exists(payload["category_id"])
    with transaction():
        for field, value in payload.items():
            setattr(product, field, value)
    return product


def update_product(product_id: int, payload: dict) -> Product:
    """PATCH semantics: only the provided fields are touched."""
    product = get_product(product_id)
    if "sku" in payload:
        _ensure_unique_sku(payload["sku"], exclude_id=product_id)
    if "category_id" in payload:
        _ensure_category_exists(payload["category_id"])
    with transaction():
        for field, value in payload.items():
            setattr(product, field, value)
    return product


def delete_product(product_id: int) -> None:
    """Delete a product, refusing to break the history of existing orders."""
    product = get_product(product_id)
    query = OrderItem.query.filter(OrderItem.product_id == product_id)
    if db.session.query(query.exists()).scalar():
        raise ConflictError(
            "Product cannot be deleted because it belongs to at least one order. "
            "Set 'is_active' to false to remove it from the catalog instead."
        )
    with transaction() as session:
        session.delete(product)


# --------------------------------------------------------------------------- #
# Helpers reused by the order service
# --------------------------------------------------------------------------- #
def get_purchasable_product(product_id: int) -> Product:
    """Return a product that may be added to an order.

    Referenced from an order payload, an unknown product is a payload problem
    (422) rather than a missing resource (404).
    """
    product = db.session.get(Product, product_id)
    if product is None:
        raise ValidationError(
            "Invalid product in items",
            {"items": [f"Product {product_id} does not exist"]},
        )
    if not product.is_active:
        raise BusinessRuleError(f"Product '{product.name}' is not available for sale")
    return product


def reserve_stock(product: Product, quantity: int) -> None:
    """Take units out of the catalog, refusing to go negative."""
    if product.stock < quantity:
        raise BusinessRuleError(
            f"Insufficient stock for product '{product.name}': "
            f"requested {quantity}, available {product.stock}"
        )
    product.stock -= quantity


def release_stock(product: Product, quantity: int) -> None:
    """Give reserved units back to the catalog."""
    product.stock += quantity


def _ensure_unique_sku(sku: str, exclude_id: int | None = None) -> None:
    """The SKU is a natural key, so duplicates are a 409."""
    query = Product.query.filter(Product.sku == sku)
    if exclude_id is not None:
        query = query.filter(Product.id != exclude_id)
    if db.session.query(query.exists()).scalar():
        raise ConflictError(f"A product with SKU '{sku}' already exists")


def _ensure_category_exists(category_id: int) -> None:
    """Validated here so the client gets a field-level 422 instead of a FK error."""
    if db.session.get(Category, category_id) is None:
        raise ValidationError(
            "Invalid category_id",
            {"category_id": [f"Category {category_id} does not exist"]},
        )
