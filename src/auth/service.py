from sqlmodel import Session, select

from src.core.security import verify_password
from src.users.models import User


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    statement = select(User).where(User.email == email)
    db_user = session.exec(statement).first()
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
