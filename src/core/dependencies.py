from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Annotated

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from src.core import security
from src.core.config import settings
from src.core.db import engine

if TYPE_CHECKING:
    from src.auth.permissions import Permission
    from src.users.models import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session]:
    """
    Database session dependency with automatic transaction management.

    - Automatically commits on successful request completion
    - Automatically rolls back on exceptions
    - Closes session after request

    Usage:
        @router.post("/items/")
        def create_item(session: SessionDep, item: ItemCreate):
            new_item = Item(**item.dict())
            session.add(new_item)
            # No need to call session.commit() - it's automatic!
            return new_item
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()  # Auto-commit on success
        except Exception:
            session.rollback()  # Auto-rollback on error
            raise


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


class PaginationParams:
    """
    Common pagination parameters for list endpoints.

    Usage:
        @router.get("/items/")
        def list_items(pagination: PaginationDep):
            query = select(Item).offset(pagination.skip).limit(pagination.limit)
            ...
    """
    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=100, ge=0, le=1000, description="Maximum number of records to return"),
    ):
        self.skip = skip
        self.limit = limit


PaginationDep = Annotated[PaginationParams, Depends()]


def get_current_user(session: SessionDep, token: TokenDep):
    from src.auth.schemas import TokenPayload
    from src.users.models import User

    # Check for empty or whitespace-only token
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated["User", Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def require_permission(*required_permissions: Permission):
    """
    Dependency factory that checks if user has required permissions.

    This enables flexible, Django/AWS IAM-style permission checking.
    Permissions are checked against the user's effective permissions,
    which combines role defaults with individual overrides.

    Usage:
        @router.post("/", dependencies=[Depends(require_permission(Permission.BOOKS_CREATE))])
        def create_book(...):
            ...

        # Multiple permissions (all required):
        @router.delete("/", dependencies=[Depends(require_permission(
            Permission.BOOKS_DELETE,
            Permission.BOOKS_READ
        ))])
        def delete_book(...):
            ...

    Args:
        *required_permissions: One or more Permission enums that are ALL required

    Returns:
        A dependency function that validates permissions
    """
    from src.auth.permissions import get_user_effective_permissions

    def permission_checker(current_user: CurrentUser):
        user_permissions = get_user_effective_permissions(current_user)

        missing_permissions = []
        for perm in required_permissions:
            if perm not in user_permissions:
                missing_permissions.append(perm.value)

        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        return current_user

    return permission_checker


def require_any_permission(*required_permissions: Permission):
    """
    Dependency factory that checks if user has ANY of the required permissions.

    Usage:
        @router.get("/", dependencies=[Depends(require_any_permission(
            Permission.BORROWS_READ,
            Permission.BORROWS_READ_ALL
        ))])
        def list_borrows(...):
            ...
    """
    from src.auth.permissions import get_user_effective_permissions

    def permission_checker(current_user: CurrentUser):
        user_permissions = get_user_effective_permissions(current_user)

        if not any(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(p.value for p in required_permissions)}"
            )
        return current_user

    return permission_checker

