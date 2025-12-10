import uuid
from datetime import datetime

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
