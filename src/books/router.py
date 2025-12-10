import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import asc, col, desc, func, select

from src.auth.permissions import Permission
from src.books import service
from src.books.models import Book
from src.books.schemas import (
    BookCreate,
    BookPublic,
    BookQueryParams,
    BooksPublic,
    BookUpdate,
)
from src.core.dependencies import CurrentUser, SessionDep, require_permission
from src.core.models import Message

router = APIRouter(prefix="/books", tags=["books"])


@router.post(
    "/",
    response_model=BookPublic,
    dependencies=[Depends(require_permission(Permission.BOOKS_CREATE))],
)
def create_book(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    book_in: BookCreate,
) -> Any:
    """
    Register a new book to the library.

    Requires: books:create permission (librarian role by default)

    Note: If a book with the same ISBN already exists, the title and author
    must match. Multiple copies of the same book (same ISBN) are allowed
    and will have different IDs.
    """
    try:
        book = service.create_book(session=session, book_create=book_in)
        return book
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=BooksPublic,
    dependencies=[Depends(require_permission(Permission.BOOKS_READ))],
)
def list_books(
    session: SessionDep,
    _current_user: CurrentUser,
    params: BookQueryParams = Depends(),
) -> Any:
    """
    Get a list of all books in the library.

    Requires: books:read permission (all authenticated users by default)

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (max 1000)
    - search: Search term for title or author (case-insensitive partial match)
    - isbn: Filter by exact ISBN
    - available_only: If true, only return books available for borrowing
    - sort: Sort field with optional - prefix for descending (e.g., 'title', '-created_at', '-author')
    """
    # Build query
    query = select(Book)

    # Apply search filter
    if params.search:
        search_term = f"%{params.search}%"
        query = query.where(
            (col(Book.title).ilike(search_term)) | (col(Book.author).ilike(search_term))
        )

    # Apply ISBN filter
    if params.isbn:
        query = query.where(Book.isbn == params.isbn)

    # Apply availability filter
    if params.available_only:
        query = query.where(Book.is_available == True)  # noqa: E712

    # Count total matching records
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Apply sorting
    sort_column = {
        "title": Book.title,
        "author": Book.author,
        "created_at": Book.created_at,
    }.get(params.sort_field, Book.title)

    if params.is_descending:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    query = query.offset(params.skip).limit(params.limit)
    books = session.exec(query).all()

    return BooksPublic(data=books, count=count)


@router.get(
    "/{book_id}",
    response_model=BookPublic,
    dependencies=[Depends(require_permission(Permission.BOOKS_READ))],
)
def get_book(
    book_id: uuid.UUID,
    session: SessionDep,
    _current_user: CurrentUser,
) -> Any:
    """
    Get a specific book by ID.

    Requires: books:read permission
    """
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.patch(
    "/{book_id}",
    response_model=BookPublic,
    dependencies=[Depends(require_permission(Permission.BOOKS_UPDATE))],
)
def update_book(
    book_id: uuid.UUID,
    session: SessionDep,
    _current_user: CurrentUser,
    book_in: BookUpdate,
) -> Any:
    """
    Update a book's information.

    Requires: books:update permission (librarian role by default)
    """
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        book = service.update_book(session=session, db_book=book, book_update=book_in)
        return book
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete(
    "/{book_id}",
    dependencies=[Depends(require_permission(Permission.BOOKS_DELETE))],
)
def delete_book(
    book_id: uuid.UUID,
    session: SessionDep,
    _current_user: CurrentUser,
) -> Message:
    """
    Delete a book from the library.

    Requires: books:delete permission (librarian role by default)

    Note: Cannot delete a book that is currently borrowed.
    """
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.is_available:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a book that is currently borrowed"
        )

    session.delete(book)
    return Message(message="Book deleted successfully")
