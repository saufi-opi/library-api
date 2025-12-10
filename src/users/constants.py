# Users module constants

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 40
MAX_EMAIL_LENGTH = 255
MAX_FULL_NAME_LENGTH = 255

USER_ERROR_MESSAGES = {
    "email_exists": "The user with this email already exists in the system.",
    "user_not_found": "The user with this id does not exist in the system",
    "insufficient_privileges": "The user doesn't have enough privileges",
    "cannot_delete_self": "Super users are not allowed to delete themselves",
    "incorrect_password": "Incorrect password",
    "same_password": "New password cannot be the same as the current one",
}
