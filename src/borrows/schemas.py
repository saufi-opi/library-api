import uuid
from datetime import datetime

from fastapi import Query
from sqlmodel import SQLModel


# Schema for borrowing a book
class BorrowCreate(SQLModel):
    """Request to borrow a book."""

    book_id: uuid.UUID


# Schema for returning a book (just needs the borrow record ID)
class ReturnCreate(SQLModel):
    """Request to return a borrowed book."""

    pass  # The borrow record ID comes from the URL path


# Properties to return via API
class BorrowRecordPublic(SQLModel):
    id: uuid.UUID
    book_id: uuid.UUID
    borrower_id: uuid.UUID
    borrowed_at: datetime
    returned_at: datetime | None


class BorrowRecordWithDetails(BorrowRecordPublic):
    """Borrow record with book and borrower details."""

    book_isbn: str
    book_title: str
    book_author: str
    borrower_name: str | None
    borrower_email: str


class BorrowRecordsPublic(SQLModel):
    data: list[BorrowRecordPublic]
    count: int


class BorrowQueryParams:
    """Query parameters for listing borrow records."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            default=100, ge=0, le=1000, description="Maximum records to return"
        ),
        active_only: bool = Query(
            default=False, description="Only show active (unreturned) borrows"
        ),
        book_id: uuid.UUID | None = Query(
            default=None, description="Filter by book ID"
        ),
        borrower_id: uuid.UUID | None = Query(
            default=None, description="Filter by borrower user ID"
        ),
        sort: str = Query(
            default="-borrowed_at",
            description="Sort by field. Prefix with - for descending. Examples: borrowed_at, -borrowed_at, -returned_at",
        ),
    ):
        self.skip = skip
        self.limit = limit
        self.active_only = active_only
        self.book_id = book_id
        self.borrower_id = borrower_id
        self.sort = sort

        # Parse sorting
        self.is_descending = sort.startswith("-")
        self.sort_field = sort.lstrip("+-")
