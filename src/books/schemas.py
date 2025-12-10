import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


# Shared properties
class BookBase(SQLModel):
    isbn: str = Field(max_length=20)
    title: str = Field(max_length=500)
    author: str = Field(max_length=255)


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
