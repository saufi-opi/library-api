import re
import uuid
from datetime import datetime

from fastapi import Query
from pydantic import field_validator
from sqlmodel import Field, SQLModel


# Shared properties
class BookBase(SQLModel):
    isbn: str = Field(max_length=20, min_length=10)
    title: str = Field(max_length=500, min_length=1)
    author: str = Field(max_length=255, min_length=1)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN format (ISBN-10 or ISBN-13)."""
        # Remove hyphens and spaces
        isbn = v.replace("-", "").replace(" ", "")

        # Check if it's valid ISBN-10 or ISBN-13 format
        if not (len(isbn) == 10 or len(isbn) == 13):
            raise ValueError("ISBN must be 10 or 13 digits (hyphens allowed)")

        # Check if it contains only digits (and X for ISBN-10)
        if len(isbn) == 10:
            if not re.match(r"^\d{9}[\dX]$", isbn):
                raise ValueError("Invalid ISBN-10 format")
        else:  # ISBN-13
            if not isbn.isdigit():
                raise ValueError("Invalid ISBN-13 format")

        return v

    @field_validator("title", "author")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that fields are not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


# Properties to receive on book creation
class BookCreate(BookBase):
    """
    Schema for registering a new book.

    Note: If a book with the same ISBN already exists,
    the title and author must match the existing book.
    """

    pass


# Properties to receive on book update
class BookUpdate(SQLModel):
    isbn: str | None = Field(default=None, max_length=20)
    title: str | None = Field(default=None, max_length=500)
    author: str | None = Field(default=None, max_length=255)
    is_available: bool | None = None


# Properties to return via API
class BookPublic(BookBase):
    id: uuid.UUID
    is_available: bool
    created_at: datetime


class BooksPublic(SQLModel):
    data: list[BookPublic]
    count: int


class BookQueryParams:
    """Query parameters for listing books."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            default=100, ge=0, le=1000, description="Maximum records to return"
        ),
        search: str | None = Query(
            default=None, description="Search in title and author"
        ),
        isbn: str | None = Query(default=None, description="Filter by exact ISBN"),
        available_only: bool = Query(
            default=False, description="Only show available books"
        ),
        sort: str = Query(
            default="title",
            description="Sort by field. Prefix with - for descending. Examples: title, -created_at, -author",
        ),
    ):
        self.skip = skip
        self.limit = limit
        self.search = search
        self.isbn = isbn
        self.available_only = available_only
        self.sort = sort

        # Parse sorting
        self.is_descending = sort.startswith("-")
        self.sort_field = sort.lstrip("+-")
