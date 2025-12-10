import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Book(SQLModel, table=True):
    """
    Represents a physical book copy in the library.

    Multiple copies of the same book (same ISBN) can exist,
    each with a unique id. Books with the same ISBN must have
    matching title and author.
    """

    __tablename__ = "book"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    isbn: str = Field(max_length=20, index=True)  # Not unique - allows multiple copies
    title: str = Field(max_length=500)
    author: str = Field(max_length=255)
    is_available: bool = Field(default=True)  # Whether book can be borrowed
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Note: Relationship to BorrowRecord will be added via TYPE_CHECKING
    # to avoid circular imports
