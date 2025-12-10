"""Tests for permission system."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.auth.permissions import (
    Permission,
    PermissionEffect,
    UserRole,
    get_user_effective_permissions,
)
from src.users.models import User, UserPermissionOverride


class TestPermissionSystem:
    """Test cases for the permission system."""

    def test_librarian_default_permissions(self, db: Session):
        """Librarians should have their default permissions."""
        user = User(
            email="librarian@test.com",
            hashed_password="hashed",
            role=UserRole.LIBRARIAN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        perms = get_user_effective_permissions(user)

        # Check librarian has book management permissions
        assert Permission.BOOKS_CREATE in perms
        assert Permission.BOOKS_READ in perms
        assert Permission.BOOKS_DELETE in perms
        assert Permission.BORROWS_READ_ALL in perms

        # Librarian should not have borrow create by default
        assert Permission.BORROWS_CREATE not in perms

    def test_member_default_permissions(self, db: Session):
        """Members should have their default permissions."""
        user = User(
            email="member@test.com",
            hashed_password="hashed",
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        perms = get_user_effective_permissions(user)

        # Check member has borrowing permissions
        assert Permission.BOOKS_READ in perms
        assert Permission.BORROWS_CREATE in perms
        assert Permission.BORROWS_RETURN in perms
        assert Permission.BORROWS_READ in perms

        # Member should not have book management permissions
        assert Permission.BOOKS_CREATE not in perms
        assert Permission.BORROWS_READ_ALL not in perms

    def test_permission_override_allow(self, db: Session):
        """Allow override should add permission."""
        user = User(
            email="member_allow@test.com",
            hashed_password="hashed",
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Add allow override for books:create
        override = UserPermissionOverride(
            user_id=user.id,
            permission=Permission.BOOKS_CREATE.value,
            effect=PermissionEffect.ALLOW,
        )
        db.add(override)
        db.commit()
        db.refresh(user)

        perms = get_user_effective_permissions(user)

        # Member should now have books:create
        assert Permission.BOOKS_CREATE in perms

    def test_permission_override_deny(self, db: Session):
        """Deny override should remove permission."""
        user = User(
            email="member_deny@test.com",
            hashed_password="hashed",
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Add deny override for borrows:create
        override = UserPermissionOverride(
            user_id=user.id,
            permission=Permission.BORROWS_CREATE.value,
            effect=PermissionEffect.DENY,
        )
        db.add(override)
        db.commit()
        db.refresh(user)

        perms = get_user_effective_permissions(user)

        # Member should no longer have borrows:create
        assert Permission.BORROWS_CREATE not in perms
        # But should still have other member permissions
        assert Permission.BOOKS_READ in perms

    def test_deny_wins_over_allow(self, db: Session):
        """Deny should take precedence when both are present."""
        user = User(
            email="both@test.com",
            hashed_password="hashed",
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Add both allow and deny for same permission
        allow = UserPermissionOverride(
            user_id=user.id,
            permission=Permission.BOOKS_CREATE.value,
            effect=PermissionEffect.ALLOW,
        )
        deny = UserPermissionOverride(
            user_id=user.id,
            permission=Permission.BOOKS_CREATE.value,
            effect=PermissionEffect.DENY,
        )
        db.add(allow)
        db.add(deny)
        db.commit()
        db.refresh(user)

        perms = get_user_effective_permissions(user)

        # Deny should win
        assert Permission.BOOKS_CREATE not in perms

    def test_superuser_has_all_permissions(self, db: Session):
        """Superusers should have all permissions regardless of role."""
        user = User(
            email="super@test.com",
            hashed_password="hashed",
            role=UserRole.MEMBER,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        perms = get_user_effective_permissions(user)

        # Superuser should have all permissions
        for perm in Permission:
            assert perm in perms


class TestPermissionEndpoints:
    """Test cases for permission management endpoints."""

    def test_get_own_permissions(
        self,
        client: TestClient,
        member_token_headers: dict,
        test_member,
    ):
        """Users should be able to view their own permissions."""
        response = client.get(
            f"/api/v1/users/{test_member.id}/permissions",
            headers=member_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "member"
        assert "effective_permissions" in data
        assert "books:read" in data["effective_permissions"]

    def test_get_other_permissions_forbidden(
        self,
        client: TestClient,
        member_token_headers: dict,
    ):
        """Non-superusers should not view others' permissions."""
        import uuid
        other_user_id = uuid.uuid4()

        response = client.get(
            f"/api/v1/users/{other_user_id}/permissions",
            headers=member_token_headers,
        )
        assert response.status_code == 403

    def test_add_permission_override_superuser(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        test_member,
    ):
        """Superusers should be able to add permission overrides."""
        response = client.post(
            f"/api/v1/users/{test_member.id}/permissions/overrides",
            headers=superuser_token_headers,
            json={
                "permission": "books:create",
                "effect": "allow",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["permission"] == "books:create"
        assert data["effect"] == "allow"

    def test_add_invalid_permission_fails(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        test_member,
    ):
        """Adding invalid permission should fail."""
        response = client.post(
            f"/api/v1/users/{test_member.id}/permissions/overrides",
            headers=superuser_token_headers,
            json={
                "permission": "invalid:permission",
                "effect": "allow",
            },
        )
        assert response.status_code == 400
        assert "Invalid permission" in response.json()["detail"]
