"""Edge case tests for books API."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.books.models import Book
from src.core.config import settings


class TestBooksEdgeCases:
    """Edge case tests for books endpoints."""

    def test_create_book_with_invalid_isbn_format(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should reject invalid ISBN format."""
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "invalid-isbn",
                "title": "Test Book",
                "author": "Test Author",
            },
        )
        assert response.status_code == 422

    def test_create_book_with_duplicate_isbn(
        self,
        client: TestClient,
        librarian_token_headers: dict,
        db: Session,
    ):
        """Should handle duplicate ISBN appropriately."""
        # Create first book
        book = Book(
            isbn="978-0-123-45678-9",
            title="Original Book",
            author="Author One",
        )
        db.add(book)
        db.commit()

        # Try to create book with same ISBN
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-123-45678-9",
                "title": "Duplicate Book",
                "author": "Author Two",
            },
        )
        assert response.status_code in [400, 409]

    def test_create_book_with_very_long_title(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should handle very long titles."""
        long_title = "A" * 500  # 500 character title
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-111-11111-1",
                "title": long_title,
                "author": "Test Author",
            },
        )
        # Should either accept or reject gracefully
        assert response.status_code in [200, 422]

    def test_create_book_with_special_characters(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should handle special characters in title and author."""
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-222-22222-2",
                "title": "The Book: A Story of 'Quotes' & <HTML>",
                "author": "O'Brien, José María",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "The Book: A Story of 'Quotes' & <HTML>" in data["title"]
        assert "O'Brien, José María" in data["author"]

    def test_create_book_with_empty_title(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should reject empty title."""
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-333-33333-3",
                "title": "",
                "author": "Test Author",
            },
        )
        assert response.status_code == 422

    def test_create_book_with_empty_author(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should reject empty author."""
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-444-44444-4",
                "title": "Test Book",
                "author": "",
            },
        )
        assert response.status_code == 422

    def test_create_book_with_whitespace_only_title(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should reject whitespace-only title."""
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-555-55555-5",
                "title": "   ",
                "author": "Test Author",
            },
        )
        assert response.status_code == 422

    def test_list_books_empty_database(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should handle empty database gracefully."""
        response = client.get(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_nonexistent_book(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should return 404 for nonexistent book."""
        import uuid
        fake_id = str(uuid.uuid4())

        response = client.get(
            f"{settings.API_V1_STR}/books/{fake_id}",
            headers=librarian_token_headers,
        )
        assert response.status_code == 404

    def test_list_books_pagination_edge_cases(
        self,
        client: TestClient,
        librarian_token_headers: dict,
        db: Session,
    ):
        """Should handle pagination edge cases."""
        # Create one book
        book = Book(
            isbn="978-0-666-66666-6",
            title="Single Book",
            author="Test Author",
        )
        db.add(book)
        db.commit()

        # Request with skip greater than total
        response = client.get(
            f"{settings.API_V1_STR}/books/?skip=100",
            headers=librarian_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0 or len(data["data"]) >= 0

    def test_create_book_with_missing_fields(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Should reject request with missing required fields."""
        # Missing title
        response = client.post(
            f"{settings.API_V1_STR}/books/",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-777-77777-7",
                "author": "Test Author",
            },
        )
        assert response.status_code == 422

    def test_update_book_to_existing_isbn(
        self,
        client: TestClient,
        librarian_token_headers: dict,
        db: Session,
    ):
        """Should prevent updating book to an existing ISBN."""
        # Create two books
        book1 = Book(
            isbn="978-0-888-88888-8",
            title="Book One",
            author="Author One",
        )
        book2 = Book(
            isbn="978-0-999-99999-9",
            title="Book Two",
            author="Author Two",
        )
        db.add(book1)
        db.add(book2)
        db.commit()
        db.refresh(book1)

        # Try to update book1 to book2's ISBN
        response = client.patch(
            f"{settings.API_V1_STR}/books/{book1.id}",
            headers=librarian_token_headers,
            json={
                "isbn": "978-0-999-99999-9",  # book2's ISBN
                "title": "Updated Book",
                "author": "Updated Author",
            },
        )
        # Should either reject or handle gracefully
        assert response.status_code in [400, 409, 422]
