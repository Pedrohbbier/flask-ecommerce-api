"""Business rules for categories."""

from app.extensions import db
from app.errors import ConflictError, ResourceNotFoundError
from app.models import Category
from app.services.pagination import apply_sorting, paginate
from app.services.transaction import transaction


def list_categories(filters: dict) -> dict:
    """Return a paginated, filtered and sorted list of categories."""
    query = Category.query
    if name := filters.get("name"):
        query = query.filter(Category.name.ilike(f"%{name}%"))

    query = apply_sorting(query, Category, filters["sort_by"], filters["order"])
    return paginate(query, filters["page"], filters["per_page"])


def get_category(category_id: int) -> Category:
    """Return a category or raise 404."""
    category = db.session.get(Category, category_id)
    if category is None:
        raise ResourceNotFoundError(f"Category {category_id} not found")
    return category


def create_category(payload: dict) -> Category:
    """Create a category. Duplicated names are rejected with 409."""
    _ensure_unique_name(payload["name"])
    category = Category(**payload)
    with transaction() as session:
        session.add(category)
    return category


def replace_category(category_id: int, payload: dict) -> Category:
    """PUT semantics: every writable field is overwritten."""
    category = get_category(category_id)
    _ensure_unique_name(payload["name"], exclude_id=category_id)
    with transaction():
        category.name = payload["name"]
        category.description = payload.get("description")
    return category


def update_category(category_id: int, payload: dict) -> Category:
    """PATCH semantics: only the provided fields are touched."""
    category = get_category(category_id)
    if "name" in payload:
        _ensure_unique_name(payload["name"], exclude_id=category_id)
    with transaction():
        for field, value in payload.items():
            setattr(category, field, value)
    return category


def delete_category(category_id: int) -> None:
    """Delete a category, refusing to orphan its products (409)."""
    category = get_category(category_id)
    if category.products.count() > 0:
        raise ConflictError(
            "Category cannot be deleted because it still has products associated "
            "with it. Move or delete those products first."
        )
    with transaction() as session:
        session.delete(category)


def _ensure_unique_name(name: str, exclude_id: int | None = None) -> None:
    """The category name is a natural key, so duplicates are a 409."""
    query = Category.query.filter(Category.name == name)
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)
    if db.session.query(query.exists()).scalar():
        raise ConflictError(f"A category named '{name}' already exists")
