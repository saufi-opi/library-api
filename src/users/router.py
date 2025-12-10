import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from src.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from src.core.models import Message
from src.core.security import get_password_hash, verify_password
from src.users import service
from src.users.schemas import (
    PermissionOverrideCreate,
    PermissionOverridePublic,
    UpdatePassword,
    UserCreate,
    UserEffectivePermissions,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    from src.users.models import User

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = service.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = service.create_user(session=session, user_create=user_in)
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = service.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.flush()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.flush()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = service.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = service.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    from src.users.models import User

    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    from src.users.models import User

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = service.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = service.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    from src.users.models import User

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.flush()
    return Message(message="User deleted successfully")


# Permission management endpoints
@router.get("/{user_id}/permissions", response_model=UserEffectivePermissions)
def get_user_effective_permissions(
    user_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Get the effective permissions for a user.

    Returns the calculated permissions based on role defaults and individual overrides.
    Users can view their own permissions; superusers can view any user's permissions.
    """
    from src.auth.permissions import get_user_effective_permissions as calc_perms
    from src.users.models import User

    # Check authorization
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own permissions"
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    effective_perms = calc_perms(user)

    return UserEffectivePermissions(
        user_id=user.id,
        role=user.role,
        effective_permissions=[p.value for p in effective_perms]
    )


@router.get(
    "/{user_id}/permissions/overrides",
    response_model=list[PermissionOverridePublic],
    dependencies=[Depends(get_current_active_superuser)],
)
def list_permission_overrides(
    user_id: uuid.UUID,
    session: SessionDep,
):
    """
    List all permission overrides for a user.

    Superuser only.
    """
    from src.users.models import User

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.permission_overrides


@router.post(
    "/{user_id}/permissions/overrides",
    response_model=PermissionOverridePublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def add_permission_override(
    user_id: uuid.UUID,
    session: SessionDep,
    override_in: PermissionOverrideCreate,
):
    """
    Add a permission override for a user.

    Superuser only.

    Use effect="allow" to grant a permission beyond role defaults.
    Use effect="deny" to revoke a permission from role defaults.
    """
    from src.auth.permissions import Permission
    from src.users.models import User, UserPermissionOverride

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate permission string
    try:
        Permission(override_in.permission)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission: {override_in.permission}. "
                   f"Valid permissions: {[p.value for p in Permission]}"
        )

    # Check if override already exists
    for existing in user.permission_overrides:
        if existing.permission == override_in.permission:
            raise HTTPException(
                status_code=400,
                detail=f"Permission override for '{override_in.permission}' already exists. "
                       "Delete it first to change the effect."
            )

    # Create override
    override = UserPermissionOverride(
        user_id=user_id,
        permission=override_in.permission,
        effect=override_in.effect,
    )
    session.add(override)
    session.flush()
    session.refresh(override)

    return override


@router.delete(
    "/{user_id}/permissions/overrides/{override_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_permission_override(
    user_id: uuid.UUID,
    override_id: uuid.UUID,
    session: SessionDep,
) -> Message:
    """
    Delete a permission override for a user.

    Superuser only.
    """
    from src.users.models import UserPermissionOverride

    override = session.get(UserPermissionOverride, override_id)
    if not override:
        raise HTTPException(status_code=404, detail="Permission override not found")

    if override.user_id != user_id:
        raise HTTPException(status_code=400, detail="Override does not belong to this user")

    session.delete(override)
    return Message(message="Permission override deleted successfully")
