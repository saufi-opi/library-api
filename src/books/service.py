from sqlmodel import Session, select

from src.books.models import Book
from src.books.schemas import BookCreate, BookUpdate


def get_book_by_isbn(session: Session, isbn: str) -> Book | None:
    """Get the first book with the given ISBN."""
    statement = select(Book).where(Book.isbn == isbn)
    return session.exec(statement).first()


def validate_isbn_consistency(session: Session, book_create: BookCreate) -> None:
    """
    Validate that if a book with the same ISBN exists,
    its title and author match the new book.

    Raises:
        ValueError: If ISBN exists with different title/author
    """
    existing = get_book_by_isbn(session, book_create.isbn)
    if existing:
        if existing.title != book_create.title:
            raise ValueError(
                f"ISBN {book_create.isbn} already exists with title '{existing.title}'. "
                f"Cannot register with different title '{book_create.title}'."
            )
        if existing.author != book_create.author:
            raise ValueError(
                f"ISBN {book_create.isbn} already exists with author '{existing.author}'. "
                f"Cannot register with different author '{book_create.author}'."
            )


def create_book(session: Session, book_create: BookCreate) -> Book:
    """
    Create a new book copy in the library.

    Validates ISBN consistency before creation.
    """
    validate_isbn_consistency(session, book_create)

    book = Book.model_validate(book_create)
    session.add(book)
    session.flush()
    session.refresh(book)
    return book


def update_book(session: Session, db_book: Book, book_update: BookUpdate) -> Book:
    """Update an existing book."""
    update_data = book_update.model_dump(exclude_unset=True)
    db_book.sqlmodel_update(update_data)
    session.add(db_book)
    session.flush()
    session.refresh(db_book)
    return db_book
