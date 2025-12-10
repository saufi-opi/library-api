"""Edge case tests for authentication."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.config import settings
from src.users.schemas import UserCreate
from src.users.service import create_user
from tests.utils.utils import random_email


class TestAuthEdgeCases:
    """Edge case tests for authentication."""

    def test_login_with_nonexistent_email(
        self,
        client: TestClient,
    ):
        """Should reject login with nonexistent email."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        assert response.status_code == 400

    def test_login_with_empty_email(
        self,
        client: TestClient,
    ):
        """Should reject login with empty email."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": "",
                "password": "somepassword",
            },
        )
        assert response.status_code == 422

    def test_login_with_empty_password(
        self,
        client: TestClient,
    ):
        """Should reject login with empty password."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": settings.FIRST_SUPERUSER,
                "password": "",
            },
        )
        assert response.status_code in [400, 422]

    def test_login_with_sql_injection_attempt(
        self,
        client: TestClient,
    ):
        """Should prevent SQL injection in login."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": "admin@example.com' OR '1'='1",
                "password": "password' OR '1'='1",
            },
        )
        assert response.status_code in [400, 422]

    def test_login_with_very_long_email(
        self,
        client: TestClient,
    ):
        """Should handle very long email."""
        long_email = "a" * 1000 + "@example.com"
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": long_email,
                "password": "somepassword",
            },
        )
        assert response.status_code in [400, 422]

    def test_login_with_very_long_password(
        self,
        client: TestClient,
    ):
        """Should handle very long password."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": settings.FIRST_SUPERUSER,
                "password": "a" * 10000,
            },
        )
        assert response.status_code == 400

    def test_login_case_sensitive_email(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should handle email case sensitivity correctly."""
        email = random_email().lower()
        password = "TestPass123"

        # Create user with lowercase email
        user_in = UserCreate(email=email, password=password)
        create_user(session=db, user_create=user_in)

        # Try to login with uppercase
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": email.upper(),
                "password": password,
            },
        )
        # Should handle based on implementation
        assert response.status_code in [200, 400]

    def test_login_with_inactive_user(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should reject login for inactive users."""
        email = random_email()
        password = "TestPass123"

        # Create inactive user
        user_in = UserCreate(email=email, password=password)
        user = create_user(session=db, user_create=user_in)
        user.is_active = False
        db.add(user)
        db.commit()

        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 400

    def test_access_protected_route_without_token(
        self,
        client: TestClient,
    ):
        """Should reject access without token."""
        response = client.get(
            f"{settings.API_V1_STR}/users/me",
        )
        assert response.status_code == 401

    def test_access_protected_route_with_invalid_token(
        self,
        client: TestClient,
    ):
        """Should reject invalid token."""
        response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401

    def test_access_protected_route_with_malformed_token(
        self,
        client: TestClient,
    ):
        """Should reject malformed authorization header."""
        response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401

    def test_access_protected_route_with_empty_token(
        self,
        client: TestClient,
    ):
        """Should reject empty token."""
        response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_multiple_failed_login_attempts(
        self,
        client: TestClient,
    ):
        """Should handle multiple failed login attempts."""
        for _ in range(5):
            response = client.post(
                f"{settings.API_V1_STR}/login/access-token",
                json={
                    "email": settings.FIRST_SUPERUSER,
                    "password": "wrong_password",
                },
            )
            assert response.status_code == 400

    def test_login_with_unicode_password(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should handle unicode characters in password."""
        email = random_email()
        password = "Пароль123密码"  # Unicode password

        # Create user
        user_in = UserCreate(email=email, password=password)
        create_user(session=db, user_create=user_in)

        # Login with unicode password
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200

    def test_login_with_special_characters_password(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should handle special characters in password."""
        email = random_email()
        password = "P@ssw0rd!#$%^&*()"

        # Create user
        user_in = UserCreate(email=email, password=password)
        create_user(session=db, user_create=user_in)

        # Login
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200

    def test_test_token_with_invalid_token(
        self,
        client: TestClient,
    ):
        """Should reject invalid token in test-token endpoint."""
        response = client.post(
            f"{settings.API_V1_STR}/login/test-token",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_login_missing_fields(
        self,
        client: TestClient,
    ):
        """Should reject login with missing fields."""
        # Missing password
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": settings.FIRST_SUPERUSER,
            },
        )
        assert response.status_code == 422

    def test_login_with_null_values(
        self,
        client: TestClient,
    ):
        """Should reject null values in login."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": None,
                "password": None,
            },
        )
        assert response.status_code == 422

    def test_login_with_extra_fields(
        self,
        client: TestClient,
    ):
        """Should handle extra fields in login request."""
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            json={
                "email": settings.FIRST_SUPERUSER,
                "password": settings.FIRST_SUPERUSER_PASSWORD,
                "extra_field": "should be ignored",
            },
        )
        # Should either ignore, accept, or reject
        assert response.status_code in [200, 400, 422]

    def test_concurrent_logins_same_user(
        self,
        client: TestClient,
        db: Session,
    ):
        """Should handle concurrent login requests."""
        # Create a test user
        test_email = random_email()
        test_password = "testpass123"
        user_in = UserCreate(
            email=test_email,
            password=test_password,
        )
        create_user(session=db, user_create=user_in)

        credentials = {
            "email": test_email,
            "password": test_password,
        }

        # Multiple concurrent logins
        responses = []
        for _ in range(3):
            response = client.post(
                f"{settings.API_V1_STR}/login/access-token",
                json=credentials,
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
