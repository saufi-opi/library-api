# Pagination utilities for API responses

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    skip: int = 0
    limit: int = 100

    class Config:
        frozen = True


class PaginatedResponse[T](BaseModel):
    """Generic paginated response model."""

    data: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    @classmethod
    def create(
        cls,
        data: list[T],
        total: int,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[T]:
        """Create a paginated response."""
        return cls(
            data=data,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(data)) < total,
        )


def calculate_pagination(total: int, skip: int = 0, limit: int = 100) -> dict[str, int]:
    """Calculate pagination metadata."""
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
        "current_page": (skip // limit) + 1 if limit > 0 else 1,
    }
