"""Edge case tests for borrows API."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.books.models import Book
from src.borrows.models import BorrowRecord
from src.core.config import settings


class TestBorrowsEdgeCases:
    """Edge case tests for borrows endpoints."""

    def test_borrow_same_book_twice(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Should prevent borrowing the same book twice."""
        # Create and borrow a book
        book = Book(
            isbn="978-1-111-11111-1",
            title="Test Book",
            author="Test Author",
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

        # Try to borrow again
        response = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=member_token_headers,
            json={"book_id": str(book.id)},
        )
        assert response.status_code == 400

    def test_borrow_with_invalid_book_id(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Should reject invalid book ID format."""
        response = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=member_token_headers,
            json={"book_id": "not-a-uuid"},
        )
        assert response.status_code == 422

    def test_return_book_twice(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Should prevent returning the same book twice."""
        # Create book and borrow record (already returned)
        book = Book(
            isbn="978-2-222-22222-2",
            title="Already Returned",
            author="Test Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        borrow = BorrowRecord(
            book_id=book.id,
            borrower_id=test_member.id,
            returned_at=datetime.now(UTC),
        )
        db.add(borrow)
        db.commit()
        db.refresh(borrow)

        # Try to return again
        response = client.post(
            f"{settings.API_V1_STR}/borrows/{borrow.id}/return",
            headers=member_token_headers,
        )
        assert response.status_code == 400

    def test_return_nonexistent_borrow(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Should return 404 for nonexistent borrow record."""
        import uuid

        fake_id = str(uuid.uuid4())

        response = client.post(
            f"{settings.API_V1_STR}/borrows/{fake_id}/return",
            headers=member_token_headers,
        )
        assert response.status_code == 404

    def test_borrow_without_authentication(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should reject borrow request without authentication."""
        book = Book(
            isbn="978-3-333-33333-3",
            title="Auth Test Book",
            author="Test Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        response = client.post(
            f"{settings.API_V1_STR}/borrows/",
            json={"book_id": str(book.id)},
        )
        assert response.status_code == 401

    def test_list_borrows_empty(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Should handle empty borrow list gracefully."""
        response = client.get(
            f"{settings.API_V1_STR}/borrows/me",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_borrow_missing_book_id(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Should reject borrow request without book_id."""
        response = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=member_token_headers,
            json={},
        )
        assert response.status_code == 422

    def test_list_borrows_pagination(
        self,
        client: TestClient,
        librarian_token_headers: dict,
        db: Session,
        test_member,
    ):
        """Should handle pagination correctly."""
        # Create multiple borrow records
        for i in range(5):
            book = Book(
                isbn=f"978-4-444-4444{i}-{i}",
                title=f"Book {i}",
                author="Test Author",
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

        # Test pagination
        response = client.get(
            f"{settings.API_V1_STR}/borrows/?skip=2&limit=2",
            headers=librarian_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_return_with_invalid_borrow_id(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Should reject invalid borrow ID format."""
        response = client.post(
            f"{settings.API_V1_STR}/borrows/not-a-uuid/return",
            headers=member_token_headers,
        )
        assert response.status_code == 422

    def test_borrow_deleted_book(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should handle borrowing a deleted book."""
        # Create a book
        book = Book(
            isbn="978-5-555-55555-5",
            title="To Be Deleted",
            author="Test Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        book_id = book.id

        # Delete the book
        db.delete(book)
        db.commit()

        # Try to borrow
        response = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=member_token_headers,
            json={"book_id": str(book_id)},
        )
        assert response.status_code == 404

    def test_concurrent_borrow_same_book(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should handle concurrent borrow attempts on same book."""
        from src.auth.permissions import UserRole
        from src.core.security import get_password_hash
        from src.users.models import User
        from tests.utils.utils import random_email

        # Create a second member user
        second_member = User(
            email=random_email(),
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            role=UserRole.MEMBER,
        )
        db.add(second_member)
        db.commit()

        # Get token for second member
        login_response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={"email": second_member.email, "password": "testpass123"},
        )
        second_member_token_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Create an available book
        book = Book(
            isbn="978-6-666-66666-6",
            title="Popular Book",
            author="Test Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        # First borrow succeeds
        response1 = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=member_token_headers,
            json={"book_id": str(book.id)},
        )
        assert response1.status_code == 200

        # Second concurrent borrow should fail (book now unavailable)
        response2 = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=second_member_token_headers,
            json={"book_id": str(book.id)},
        )
        assert response2.status_code == 400

    def test_borrow_record_timestamps(
        self,
        client: TestClient,
        member_token_headers: dict,
        db: Session,
    ):
        """Should set correct timestamps on borrow."""
        book = Book(
            isbn="978-7-777-77777-7",
            title="Timestamp Test",
            author="Test Author",
            is_available=True,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        before_borrow = datetime.now(UTC)

        response = client.post(
            f"{settings.API_V1_STR}/borrows/",
            headers=member_token_headers,
            json={"book_id": str(book.id)},
        )

        after_borrow = datetime.now(UTC)

        assert response.status_code == 200
        data = response.json()
        assert "borrowed_at" in data
        assert data["returned_at"] is None

        # Verify timestamp is reasonable
        borrowed_at_str = data["borrowed_at"]
        # Handle both 'Z' and '+00:00' timezone formats
        if borrowed_at_str.endswith("Z"):
            borrowed_at_str = borrowed_at_str.replace("Z", "+00:00")
        borrowed_at = datetime.fromisoformat(borrowed_at_str)
        # Ensure timezone-aware comparison
        if borrowed_at.tzinfo is None:
            borrowed_at = borrowed_at.replace(tzinfo=UTC)
        assert before_borrow <= borrowed_at <= after_borrow
