# Permissions module for role-based access control
# Inspired by Django permissions and AWS IAM

from enum import Enum


class Permission(str, Enum):
    """
    Granular permissions for the library system.
    Naming convention: resource:action
    """

    # Books permissions
    BOOKS_CREATE = "books:create"
    BOOKS_READ = "books:read"
    BOOKS_UPDATE = "books:update"
    BOOKS_DELETE = "books:delete"

    # Borrows permissions
    BORROWS_CREATE = "borrows:create"  # Borrow a book
    BORROWS_RETURN = "borrows:return"  # Return a borrowed book
    BORROWS_READ = "borrows:read"  # View own borrow records
    BORROWS_READ_ALL = "borrows:read_all"  # View all borrow records

    # Users permissions
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"


class UserRole(str, Enum):
    """User roles with default permission sets."""

    LIBRARIAN = "librarian"
    MEMBER = "member"


class PermissionEffect(str, Enum):
    """Effect of a permission override."""

    ALLOW = "allow"
    DENY = "deny"


# Role → Default Permissions mapping
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.LIBRARIAN: {
        Permission.BOOKS_CREATE,
        Permission.BOOKS_READ,
        Permission.BOOKS_UPDATE,
        Permission.BOOKS_DELETE,
        Permission.BORROWS_READ,
        Permission.BORROWS_READ_ALL,
        Permission.USERS_READ,
    },
    UserRole.MEMBER: {
        Permission.BOOKS_READ,
        Permission.BORROWS_CREATE,
        Permission.BORROWS_RETURN,
        Permission.BORROWS_READ,
    },
}


def get_user_effective_permissions(user) -> set[Permission]:
    """
    Calculate effective permissions for a user.

    Algorithm:
    1. Start with role default permissions
    2. Apply user-level overrides (allow adds, deny removes)
    3. Superuser gets all permissions

    Note: Deny always wins over allow.

    Args:
        user: User object with role and permission_overrides attributes

    Returns:
        Set of effective Permission enums
    """
    # Superuser has all permissions
    if user.is_superuser:
        return set(Permission)

    # Start with role defaults
    permissions = ROLE_PERMISSIONS.get(user.role, set()).copy()

    # Collect allows and denies separately
    allows: set[Permission] = set()
    denies: set[Permission] = set()

    for override in user.permission_overrides:
        try:
            perm = Permission(override.permission)
            if override.effect == PermissionEffect.ALLOW:
                allows.add(perm)
            elif override.effect == PermissionEffect.DENY:
                denies.add(perm)
        except ValueError:
            # Invalid permission string, skip
            continue

    # Apply allows first
    permissions.update(allows)

    # Then apply denies (deny wins)
    permissions -= denies

    return permissions


def has_permission(user, permission: Permission) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: User object
        permission: Permission to check

    Returns:
        True if user has the permission, False otherwise
    """
    return permission in get_user_effective_permissions(user)


def has_any_permission(user, permissions: list[Permission]) -> bool:
    """Check if user has any of the given permissions."""
    user_perms = get_user_effective_permissions(user)
    return any(p in user_perms for p in permissions)


def has_all_permissions(user, permissions: list[Permission]) -> bool:
    """Check if user has all of the given permissions."""
    user_perms = get_user_effective_permissions(user)
    return all(p in user_perms for p in permissions)
