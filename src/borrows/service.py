import uuid
from datetime import UTC, datetime

from sqlmodel import Session, col, desc, select

from src.books.models import Book
from src.borrows.models import BorrowRecord


class BookNotFoundError(Exception):
    """Raised when a book is not found."""

    pass


class BookNotAvailableError(Exception):
    """Raised when trying to borrow a book that is not available."""

    pass


class BorrowRecordNotFoundError(Exception):
    """Raised when a borrow record is not found."""

    pass


class BookAlreadyReturnedError(Exception):
    """Raised when trying to return a book that was already returned."""

    pass


class NotBorrowerError(Exception):
    """Raised when a user tries to return a book they didn't borrow."""

    pass


def get_active_borrow_for_book(
    session: Session, book_id: uuid.UUID
) -> BorrowRecord | None:
    """Get the active (not returned) borrow record for a book."""
    statement = select(BorrowRecord).where(
        BorrowRecord.book_id == book_id,
        BorrowRecord.returned_at == None,  # noqa: E711
    )
    return session.exec(statement).first()


def borrow_book(
    session: Session,
    book_id: uuid.UUID,
    borrower_id: uuid.UUID,
) -> BorrowRecord:
    """
    Borrow a book for a user.

    Args:
        session: Database session
        book_id: ID of the book to borrow
        borrower_id: ID of the user borrowing the book

    Returns:
        The created BorrowRecord

    Raises:
        BookNotFoundError: If the book doesn't exist
        BookNotAvailableError: If the book is already borrowed
    """
    # Check book exists
    book = session.get(Book, book_id)
    if not book:
        raise BookNotFoundError(f"Book with id {book_id} not found")

    # Check book is available
    if not book.is_available:
        raise BookNotAvailableError(
            f"Book '{book.title}' (ID: {book_id}) is not available for borrowing"
        )

    # Check no active borrow exists (double-check)
    active_borrow = get_active_borrow_for_book(session, book_id)
    if active_borrow:
        raise BookNotAvailableError(f"Book '{book.title}' is already borrowed")

    # Create borrow record
    borrow_record = BorrowRecord(
        book_id=book_id,
        borrower_id=borrower_id,
    )
    session.add(borrow_record)

    # Mark book as unavailable
    book.is_available = False
    session.add(book)

    session.flush()
    session.refresh(borrow_record)

    return borrow_record


def return_book(
    session: Session,
    borrow_record_id: uuid.UUID,
    returning_user_id: uuid.UUID,
) -> BorrowRecord:
    """
    Return a borrowed book.

    Args:
        session: Database session
        borrow_record_id: ID of the borrow record
        returning_user_id: ID of the user returning the book

    Returns:
        The updated BorrowRecord

    Raises:
        BorrowRecordNotFoundError: If the borrow record doesn't exist
        BookAlreadyReturnedError: If the book was already returned
        NotBorrowerError: If the user didn't borrow this book
    """
    # Get borrow record
    borrow_record = session.get(BorrowRecord, borrow_record_id)
    if not borrow_record:
        raise BorrowRecordNotFoundError(
            f"Borrow record with id {borrow_record_id} not found"
        )

    # Check not already returned
    if borrow_record.returned_at is not None:
        raise BookAlreadyReturnedError("This book has already been returned")

    # Check the returning user is the borrower
    if borrow_record.borrower_id != returning_user_id:
        raise NotBorrowerError("You can only return books that you borrowed")

    # Update borrow record
    borrow_record.returned_at = datetime.now(UTC)
    session.add(borrow_record)

    # Mark book as available
    book = session.get(Book, borrow_record.book_id)
    if book:
        book.is_available = True
        session.add(book)

    session.flush()
    session.refresh(borrow_record)

    return borrow_record


def get_user_borrow_records(
    session: Session,
    user_id: uuid.UUID,
    active_only: bool = False,
) -> list[BorrowRecord]:
    """Get all borrow records for a user."""
    query = select(BorrowRecord).where(BorrowRecord.borrower_id == user_id)

    if active_only:
        query = query.where(BorrowRecord.returned_at == None)  # noqa: E711

    query = query.order_by(desc(col(BorrowRecord.borrowed_at)))

    return list(session.exec(query).all())
