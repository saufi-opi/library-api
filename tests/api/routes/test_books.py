"""Tests for books API endpoints."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.books.models import Book


class TestBooksAPI:
    """Test cases for books endpoints."""

    def test_create_book_as_librarian(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Librarians should be able to create books."""
        response = client.post(
            "/api/v1/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-13-468599-1",
                "title": "The Pragmatic Programmer",
                "author": "David Thomas",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["isbn"] == "978-0-13-468599-1"
        assert data["title"] == "The Pragmatic Programmer"
        assert data["is_available"] is True

    def test_create_book_as_member_forbidden(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Members should not be able to create books."""
        response = client.post(
            "/api/v1/books/",
            headers=member_token_headers,
            json={
                "isbn": "978-0-13-468599-1",
                "title": "The Pragmatic Programmer",
                "author": "David Thomas",
            },
        )
        assert response.status_code == 403

    def test_list_books(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Any authenticated user should be able to list books."""
        # Create a test book
        book = Book(
            isbn="978-1-234-56789-0",
            title="Test Book",
            author="Test Author",
        )
        db.add(book)
        db.commit()

        response = client.get(
            "/api/v1/books/",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_get_book_by_id(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should be able to get a book by ID."""
        book = Book(
            isbn="978-1-234-56789-0",
            title="Test Book",
            author="Test Author",
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        response = client.get(
            f"/api/v1/books/{book.id}",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(book.id)
        assert data["title"] == "Test Book"

    def test_isbn_consistency_same_title_author(
        self,
        client: TestClient,
        librarian_token_headers: dict,
        db: Session,
    ):
        """Creating books with same ISBN should require same title/author."""
        # Create first book
        book1 = Book(
            isbn="978-0-596-52068-7",
            title="Same Title",
            author="Same Author",
        )
        db.add(book1)
        db.commit()

        # Create second book with same ISBN - should succeed with same title/author
        response = client.post(
            "/api/v1/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-596-52068-7",
                "title": "Same Title",
                "author": "Same Author",
            },
        )
        assert response.status_code == 200

    def test_isbn_consistency_different_title_fails(
        self,
        client: TestClient,
        librarian_token_headers: dict,
        db: Session,
    ):
        """Creating book with same ISBN but different title should fail."""
        # Create first book
        book1 = Book(
            isbn="978-0-321-56384-2",
            title="Original Title",
            author="Author",
        )
        db.add(book1)
        db.commit()

        # Try to create book with same ISBN but different title
        response = client.post(
            "/api/v1/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-321-56384-2",
                "title": "Different Title",
                "author": "Author",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_filter_available_books(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should be able to filter for available books only."""
        # Create available and unavailable books
        available = Book(isbn="978-1-449-35573-9", title="Available", author="A", is_available=True)
        unavailable = Book(isbn="978-0-262-03384-8", title="Unavailable", author="B", is_available=False)
        db.add(available)
        db.add(unavailable)
        db.commit()

        response = client.get(
            "/api/v1/books/?available_only=true",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for book in data["data"]:
            assert book["is_available"] is True
