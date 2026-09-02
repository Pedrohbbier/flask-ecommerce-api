"""Pagination helper shared by every listing service."""

from sqlalchemy import asc, desc


def apply_sorting(query, model, sort_by: str, order: str):
    """Order a query by a whitelisted column name."""
    column = getattr(model, sort_by, None)
    if column is None:
        column = model.id
    direction = desc if order == "desc" else asc
    return query.order_by(direction(column))


def paginate(query, page: int, per_page: int) -> dict:
    """Run the query and return items plus pagination metadata."""
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": result.items,
        "pagination": {
            "page": result.page,
            "per_page": result.per_page,
            "total_items": result.total,
            "total_pages": result.pages,
            "has_next": result.has_next,
            "has_prev": result.has_prev,
        },
    }
