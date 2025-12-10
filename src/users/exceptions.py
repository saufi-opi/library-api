# Users module exceptions

from fastapi import HTTPException, status


class UserAlreadyExistsError(HTTPException):
    """Raised when a user with the same email already exists."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )


class UserNotFoundError(HTTPException):
    """Raised when a user is not found."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )


class InsufficientPrivilegesError(HTTPException):
    """Raised when user doesn't have sufficient privileges."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )


class CannotDeleteSelfError(HTTPException):
    """Raised when superuser tries to delete themselves."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )


class IncorrectPasswordError(HTTPException):
    """Raised when password is incorrect."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )


class SamePasswordError(HTTPException):
    """Raised when new password is the same as current password."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current one",
        )
