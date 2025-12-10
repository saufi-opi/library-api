import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from src.auth.permissions import PermissionEffect, UserRole

if TYPE_CHECKING:
    from src.borrows.models import BorrowRecord


class UserPermissionOverride(SQLModel, table=True):
    """
    Individual permission overrides for a user.

    Allows granting or denying specific permissions beyond role defaults.
    Similar to AWS IAM inline policies.
    """
    __tablename__ = "user_permission_override"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    permission: str = Field(max_length=100)  # e.g., "books:create"
    effect: PermissionEffect = Field(default=PermissionEffect.ALLOW)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationship back to user
    user: "User" = Relationship(back_populates="permission_overrides")


# Database model, database table inferred from class name
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str

    # Role for default permissions
    role: UserRole = Field(default=UserRole.MEMBER)

    # Relationships
    permission_overrides: list[UserPermissionOverride] = Relationship(
        back_populates="user", cascade_delete=True
    )
    borrow_records: list["BorrowRecord"] = Relationship(back_populates="borrower")
