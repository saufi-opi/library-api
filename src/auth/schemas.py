from pydantic import EmailStr
from sqlmodel import SQLModel


class LoginAccessToken(SQLModel):
    email: EmailStr
    password: str

# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
