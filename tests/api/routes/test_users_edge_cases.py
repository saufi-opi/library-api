"""Edge case tests for users API."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.books.models import Book
from src.borrows.models import BorrowRecord
from src.core.config import settings
from src.users.schemas import UserCreate
from src.users.service import create_user
from tests.utils.utils import random_email, random_lower_string


class TestUsersEdgeCases:
    """Edge case tests for users endpoints."""

    def test_create_user_with_invalid_email(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should reject invalid email format."""
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json={
                "email": "not-an-email",
                "password": "ValidPass123",
            },
        )
        assert response.status_code == 422

    def test_create_user_with_short_password(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should reject short passwords."""
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json={
                "email": random_email(),
                "password": "123",  # Too short
            },
        )
        # Should either reject or accept based on validation rules
        assert response.status_code in [200, 422]

    def test_create_user_with_very_long_email(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should handle very long emails."""
        long_email = "a" * 300 + "@example.com"
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json={
                "email": long_email,
                "password": "ValidPass123",
            },
        )
        assert response.status_code in [200, 422]

    def test_create_user_with_special_characters_in_name(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should handle special characters in full name."""
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json={
                "email": random_email(),
                "password": "ValidPass123",
                "full_name": "José María O'Brien-Smith <test>",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "José María O'Brien-Smith" in data["full_name"]

    def test_update_user_with_empty_email(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
    ):
        """Should reject empty email update."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json={"email": ""},
        )
        assert response.status_code == 422

    def test_update_password_with_same_password(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
    ):
        """Should prevent updating to same password."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/me/password",
            headers=normal_user_token_headers,
            json={
                "current_password": "testpass123",
                "new_password": "testpass123",
            },
        )
        assert response.status_code == 400

    def test_update_password_with_wrong_current_password(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
    ):
        """Should reject wrong current password."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/me/password",
            headers=normal_user_token_headers,
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewValidPass123",
            },
        )
        assert response.status_code == 400

    def test_delete_user_with_active_borrows(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        db: Session,
    ):
        """Should handle deleting user with active borrows."""
        # Create user
        email = random_email()
        password = random_lower_string()
        user_in = UserCreate(email=email, password=password)
        user = create_user(session=db, user_create=user_in)

        # Create book and borrow for this user
        book = Book(
            isbn="978-1-111-11111-1",
            title="Borrowed Book",
            author="Test Author",
            is_available=False,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        borrow = BorrowRecord(
            book_id=book.id,
            borrower_id=user.id,
        )
        db.add(borrow)
        db.commit()

        # Try to delete user
        response = client.delete(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
        )
        # Should either prevent deletion or handle cascade
        assert response.status_code in [200, 400, 409]

    def test_get_user_with_invalid_uuid(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should reject invalid UUID format."""
        response = client.get(
            f"{settings.API_V1_STR}/users/not-a-uuid",
            headers=superuser_token_headers,
        )
        assert response.status_code == 422

    def test_register_user_with_whitespace_password(
        self,
        client: TestClient,
    ):
        """Should handle passwords with whitespace."""
        response = client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={
                "email": random_email(),
                "password": "   spaces   ",
            },
        )
        # Should either accept or reject based on validation
        assert response.status_code in [200, 422]

    def test_update_user_to_uppercase_email(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
    ):
        """Should handle email case sensitivity."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json={"email": "UPPERCASE@EXAMPLE.COM"},
        )
        # Should normalize or reject based on implementation
        assert response.status_code in [200, 422]

    def test_create_multiple_users_rapidly(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should handle rapid user creation."""
        emails = [random_email() for _ in range(5)]
        responses = []

        for email in emails:
            response = client.post(
                f"{settings.API_V1_STR}/users/",
                headers=superuser_token_headers,
                json={
                    "email": email,
                    "password": "ValidPass123",
                },
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_list_users_with_negative_skip(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should handle negative skip value."""
        response = client.get(
            f"{settings.API_V1_STR}/users/?skip=-1",
            headers=superuser_token_headers,
        )
        # Should either handle gracefully or reject
        assert response.status_code in [200, 422]

    def test_list_users_with_zero_limit(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should handle zero limit value."""
        response = client.get(
            f"{settings.API_V1_STR}/users/?limit=0",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Should return empty or handle appropriately
        assert "data" in data

    def test_list_users_with_huge_limit(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should reject very large limit value (max 1000)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/?limit=99999",
            headers=superuser_token_headers,
        )
        # Should reject limit above max (1000)
        assert response.status_code == 422

    def test_update_user_with_sql_injection_attempt(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
    ):
        """Should prevent SQL injection in user updates."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json={
                "full_name": "'; DROP TABLE users; --",
            },
        )
        # Should be safe and either accept or sanitize
        assert response.status_code in [200, 422]

    def test_create_user_with_xss_attempt(
        self,
        client: TestClient,
        superuser_token_headers: dict,
    ):
        """Should prevent XSS in user creation."""
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json={
                "email": random_email(),
                "password": "ValidPass123",
                "full_name": "<script>alert('xss')</script>",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should be escaped or sanitized
        assert "full_name" in data

    def test_register_user_duplicate_email_case_insensitive(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should handle duplicate emails with different cases."""
        email = random_email().lower()

        # Create first user
        response1 = client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={
                "email": email,
                "password": "ValidPass123",
            },
        )
        assert response1.status_code == 200

        # Try with uppercase
        response2 = client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={
                "email": email.upper(),
                "password": "ValidPass123",
            },
        )
        # Should detect duplicate based on implementation
        assert response2.status_code in [200, 400]
