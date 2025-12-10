import uuid
from datetime import datetime

from fastapi import Query
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from src.auth.permissions import PermissionEffect, UserRole


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.MEMBER)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)
    role: UserRole | None = None  # type: ignore


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Permission override schemas
class PermissionOverrideBase(SQLModel):
    permission: str = Field(max_length=100)
    effect: PermissionEffect = Field(default=PermissionEffect.ALLOW)


class PermissionOverrideCreate(PermissionOverrideBase):
    pass


class PermissionOverridePublic(PermissionOverrideBase):
    id: uuid.UUID
    created_at: datetime


# Properties to return via API
class UserPublic(UserBase):
    id: uuid.UUID


class UserWithPermissions(UserPublic):
    """User with their permission overrides."""

    permission_overrides: list[PermissionOverridePublic] = []


class UserEffectivePermissions(SQLModel):
    """Response showing user's calculated effective permissions."""

    user_id: uuid.UUID
    role: UserRole
    effective_permissions: list[str]  # List of permission strings


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UserQueryParams:
    """Query parameters for listing users."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            default=100, ge=0, le=1000, description="Maximum records to return"
        ),
        search: str | None = Query(default=None, description="Search in email"),
        role: str | None = Query(
            default=None, description="Filter by role (librarian/member)"
        ),
        is_active: bool | None = Query(
            default=None, description="Filter by active status"
        ),
        sort: str = Query(
            default="email",
            description="Sort by field. Prefix with - for descending. Examples: email, -role, -is_active",
        ),
    ):
        self.skip = skip
        self.limit = limit
        self.search = search
        self.role = role
        self.is_active = is_active
        self.sort = sort

        # Parse sorting
        self.is_descending = sort.startswith("-")
        self.sort_field = sort.lstrip("+-")
