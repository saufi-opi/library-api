"""Pytest fixtures for testing."""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from src.auth.permissions import UserRole
from src.books.models import Book
from src.borrows.models import BorrowRecord
from src.core.config import settings
from src.core.db import engine
from src.core.security import get_password_hash
from src.main import app
from src.users.models import User, UserPermissionOverride


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Database session fixture with cleanup."""
    with Session(engine) as session:
        yield session
        # Cleanup after each test
        session.exec(delete(BorrowRecord))  # type: ignore
        session.exec(delete(Book))  # type: ignore
        session.exec(delete(UserPermissionOverride))  # type: ignore
        # Don't delete users to preserve test users
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def test_superuser(_client: TestClient) -> User:
    """Create or get a superuser for testing."""
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == "superuser@test.com")
        ).first()
        if not user:
            user = User(
                email="superuser@test.com",
                hashed_password=get_password_hash("testpass123"),
                is_superuser=True,
                is_active=True,
                role=UserRole.LIBRARIAN,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user


@pytest.fixture(scope="module")
def test_librarian(_client: TestClient) -> User:
    """Create or get a librarian for testing."""
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == "librarian@test.com")
        ).first()
        if not user:
            user = User(
                email="librarian@test.com",
                hashed_password=get_password_hash("testpass123"),
                is_superuser=False,
                is_active=True,
                role=UserRole.LIBRARIAN,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user


@pytest.fixture(scope="module")
def test_member(_client: TestClient) -> User:
    """Create or get a member for testing."""
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == "member@test.com")
        ).first()
        if not user:
            user = User(
                email="member@test.com",
                hashed_password=get_password_hash("testpass123"),
                is_superuser=False,
                is_active=True,
                role=UserRole.MEMBER,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user


def get_token_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    """Get authentication token headers."""
    response = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient, _test_superuser: User) -> dict[str, str]:
    """Get superuser authentication headers."""
    return get_token_headers(client, "superuser@test.com", "testpass123")


@pytest.fixture(scope="module")
def librarian_token_headers(client: TestClient, _test_librarian: User) -> dict[str, str]:
    """Get librarian authentication headers."""
    return get_token_headers(client, "librarian@test.com", "testpass123")


@pytest.fixture(scope="module")
def member_token_headers(client: TestClient, _test_member: User) -> dict[str, str]:
    """Get member authentication headers."""
    return get_token_headers(client, "member@test.com", "testpass123")
