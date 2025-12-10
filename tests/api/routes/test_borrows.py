"""Tests for borrows API endpoints."""
from datetime import UTC

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.books.models import Book
from src.borrows.models import BorrowRecord


class TestBorrowsAPI:
    """Test cases for borrows endpoints."""

    def test_borrow_book(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Members should be able to borrow available books."""
        # Create a test book
        book = Book(
            isbn="978-1-111-11111-1",
            title="Borrowable Book",
            author="Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        response = client.post(
            "/api/v1/borrows/",
            headers=member_token_headers,
            json={"book_id": str(book.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == str(book.id)
        assert data["returned_at"] is None

        # Verify book is now unavailable
        db.refresh(book)
        assert book.is_available is False

    def test_borrow_unavailable_book_fails(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should not be able to borrow an unavailable book."""
        book = Book(
            isbn="978-2-222-22222-2",
            title="Unavailable Book",
            author="Author",
            is_available=False,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        response = client.post(
            "/api/v1/borrows/",
            headers=member_token_headers,
            json={"book_id": str(book.id)},
        )
        assert response.status_code == 400
        assert "not available" in response.json()["detail"]

    def test_borrow_nonexistent_book_fails(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Should not be able to borrow a non-existent book."""
        import uuid
        fake_id = str(uuid.uuid4())

        response = client.post(
            "/api/v1/borrows/",
            headers=member_token_headers,
            json={"book_id": fake_id},
        )
        assert response.status_code == 404

    def test_return_book(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Members should be able to return books they borrowed."""
        # Create book and borrow record
        book = Book(
            isbn="978-3-333-33333-3",
            title="Return Book",
            author="Author",
            is_available=False,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        borrow = BorrowRecord(
            book_id=book.id,
            borrower_id=test_member.id,
        )
        db.add(borrow)
        db.commit()
        db.refresh(borrow)

        response = client.post(
            f"/api/v1/borrows/{borrow.id}/return",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["returned_at"] is not None

        # Verify book is now available
        db.refresh(book)
        assert book.is_available is True

    def test_return_book_not_borrower_fails(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should not be able to return a book borrowed by someone else."""
        import uuid

        # Create book borrowed by different user
        book = Book(
            isbn="978-4-444-44444-4",
            title="Other Book",
            author="Author",
            is_available=False,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        # Borrow record for a different user
        borrow = BorrowRecord(
            book_id=book.id,
            borrower_id=uuid.uuid4(),  # Different user
        )
        db.add(borrow)
        db.commit()
        db.refresh(borrow)

        response = client.post(
            f"/api/v1/borrows/{borrow.id}/return",
            headers=member_token_headers,
        )
        assert response.status_code == 403

    def test_return_already_returned_fails(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Should not be able to return an already returned book."""
        from datetime import datetime

        book = Book(
            isbn="978-5-555-55555-5",
            title="Returned Book",
            author="Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        # Already returned borrow record
        borrow = BorrowRecord(
            book_id=book.id,
            borrower_id=test_member.id,
            returned_at=datetime.now(UTC),
        )
        db.add(borrow)
        db.commit()
        db.refresh(borrow)

        response = client.post(
            f"/api/v1/borrows/{borrow.id}/return",
            headers=member_token_headers,
        )
        assert response.status_code == 400
        assert "already been returned" in response.json()["detail"]

    def test_list_my_borrows(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Members should be able to list their own borrow records."""
        book = Book(
            isbn="978-6-666-66666-6",
            title="My Book",
            author="Author",
            is_available=False,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        borrow = BorrowRecord(
            book_id=book.id,
            borrower_id=test_member.id,
        )
        db.add(borrow)
        db.commit()

        response = client.get(
            "/api/v1/borrows/me",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1

    def test_list_all_borrows_as_librarian(
        self,
        client: TestClient,
        librarian_token_headers: dict,
    ):
        """Librarians should be able to list all borrow records."""
        response = client.get(
            "/api/v1/borrows/",
            headers=librarian_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_list_all_borrows_as_member_forbidden(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Members should not be able to list all borrow records."""
        response = client.get(
            "/api/v1/borrows/",
            headers=member_token_headers,
        )
        assert response.status_code == 403
