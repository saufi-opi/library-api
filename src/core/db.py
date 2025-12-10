from sqlmodel import Session, create_engine, select

from src.books.models import Book  # noqa: F401
from src.borrows.models import BorrowRecord  # noqa: F401
from src.core.config import settings
from src.users import service
from src.users.models import User, UserPermissionOverride  # noqa: F401
from src.users.schemas import UserCreate

# Import all SQLModel models to ensure SQLAlchemy can resolve relationships
# This must happen before any database operations

# Create database engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Maximum number of connections to create beyond pool_size
)


def get_session() -> Session:
    """Get a database session."""
    return Session(engine)


# make sure all SQLModel models are imported (src.core.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from src.core.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = service.create_user(session=session, user_create=user_in)
