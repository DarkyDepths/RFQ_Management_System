"""
Pagination helpers.

Provides:
- PaginationParams    — Pydantic model for page/size/sort query params
- paginated_response  — wraps a query result list into { data, total, page, size }
- apply_pagination    — applies OFFSET/LIMIT/ORDER BY to a SQLAlchemy query
"""

from dataclasses import dataclass


MAX_PAGE_SIZE = 100  # prevent someone requesting ?size=999999


@dataclass
class PaginationParams:
    """
    Holds page number and page size.
    Size is capped at MAX_PAGE_SIZE to prevent abuse.
    """
    page: int = 1
    size: int = 20

    def __post_init__(self):
        # Ensure valid values
        if self.page < 1:
            self.page = 1
        if self.size < 1:
            self.size = 1
        if self.size > MAX_PAGE_SIZE:
            self.size = MAX_PAGE_SIZE

    @property
    def offset(self) -> int:
        """How many rows to skip. Page 3, size 20 → skip 40."""
        return (self.page - 1) * self.size


def paginate(query, params: PaginationParams) -> tuple:
    """
    Apply pagination to a SQLAlchemy query.

    Returns (items, total_count):
      - items: the rows for this page
      - total_count: total rows matching the filter (for "total: 96" in response)

    Why count before paginating?
    Because the frontend needs to know "there are 96 total results"
    to show "page 1 of 5" — but we only return 20 rows at a time.
    """
    total = query.count()
    items = query.offset(params.offset).limit(params.size).all()
    return items, total


def paginated_response(items: list, total: int, params: PaginationParams) -> dict:
    """
    Wrap results in the standard paginated format.
    This is what the API returns:
    {
      "data": [...],
      "total": 96,
      "page": 1,
      "size": 20
    }
    """
    return {
        "data": items,
        "total": total,
        "page": params.page,
        "size": params.size,
    }
