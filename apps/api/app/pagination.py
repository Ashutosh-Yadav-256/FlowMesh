"""
FlowMesh Pagination Abstraction

Provides reusable pagination parameters and response helpers for bounded query execution.
Sets standard pagination headers (X-Total-Count, X-Page, X-Page-Size, X-Total-Pages)
while supporting both direct sliced lists and generic PaginatedResponse envelopes.
"""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar
from fastapi import Query, Response
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams:
    """FastAPI dependency for page-based query pagination."""

    def __init__(
        self,
        page: int = Query(1, ge=1, le=1000, description="Page number (1-indexed)"),
        page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


def paginate_items(
    items: List[T],
    total: int,
    params: PaginationParams,
    response: Optional[Response] = None,
) -> List[T]:
    """
    Sets standard pagination headers on the response and returns the sliced items.
    """
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 1

    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(params.page)
        response.headers["X-Page-Size"] = str(params.page_size)
        response.headers["X-Total-Pages"] = str(total_pages)

    return items
