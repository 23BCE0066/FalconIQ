"""
Common: Pagination

Provides PageRequest (query params) and PageResponse (response envelope)
reused by every list endpoint. Import from here — never redefine.

Usage:
    @router.get("/customers")
    async def list_customers(
        pagination: Annotated[PageRequest, Depends()],
    ) -> dict:
        items, total = svc.list(page=pagination.page, page_size=pagination.page_size)
        return ctx.ok(pagination.wrap(ResponseMapper.customers(items), total))
"""
import math
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class PageRequest:
    """
    Dependency-injectable pagination parameters.

    Injected via FastAPI Depends() — query params are extracted automatically.
    """

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(
            default=50,
            ge=1,
            le=200,
            description="Items per page (max 200)",
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def skip(self) -> int:
        """SQLAlchemy-compatible OFFSET value."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """SQLAlchemy-compatible LIMIT value."""
        return self.page_size

    def wrap(self, items: List[T], total_items: int) -> "PageResponse":
        """Wraps a list of items with pagination metadata."""
        return PageResponse(
            items=items,
            total_items=total_items,
            total_pages=math.ceil(total_items / self.page_size) if self.page_size else 1,
            page=self.page,
            page_size=self.page_size,
            has_next=self.page < math.ceil(total_items / self.page_size) if self.page_size else False,
            has_previous=self.page > 1,
        )


class PageResponse(BaseModel, Generic[T]):
    """
    Generic paginated response container.

    Embedded inside the standard SuccessEnvelope.data field.
    """
    items: List[T]
    total_items: int = Field(description="Total number of matching records")
    total_pages: int = Field(description="Total number of pages")
    page: int = Field(description="Current page (1-indexed)")
    page_size: int = Field(description="Items per page")
    has_next: bool = Field(default=False, description="Whether a next page exists")
    has_previous: bool = Field(default=False, description="Whether a previous page exists")
