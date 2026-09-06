"""
Auth dependencies: extract and validate the current user from a Bearer
JWT, and gate admin-only endpoints.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.models.schemas import UserOut, UserRole
from app.services.user_store import get_user_store

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().API_V1_PREFIX}/auth/login"
)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserOut:
    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise _CREDENTIALS_EXCEPTION
    except JWTError as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    store = get_user_store()
    user = store.get_user_out(username)
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user


async def get_current_admin(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires administrator privileges.",
        )
    return current_user
