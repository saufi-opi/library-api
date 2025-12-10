import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.users.models import User


class BorrowRecord(SQLModel, table=True):
    """
    Represents a book borrowing transaction.

    Tracks when a book was borrowed and returned.
    A book can only be borrowed by one user at a time.
    """
    __tablename__ = "borrow_record"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign keys
    book_id: uuid.UUID = Field(foreign_key="book.id", nullable=False)
    borrower_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)

    # Timestamps
    borrowed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    returned_at: datetime | None = Field(default=None)

    # Relationships
    borrower: "User" = Relationship(back_populates="borrow_records")
