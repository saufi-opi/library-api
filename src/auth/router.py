from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from src.auth import service
from src.auth.schemas import LoginAccessToken, Token
from src.core import security
from src.core.config import settings
from src.core.dependencies import CurrentUser, SessionDep
from src.users.schemas import UserPublic

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, body: LoginAccessToken
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = service.authenticate(
        session=session, email=body.email, password=body.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user
