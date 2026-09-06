"""
Authentication routes: registration, login, and current-user lookup.

New accounts always register with role=user. The admin role is only ever
granted via the seeded default admin account (see user_store.py) or by
direct database edit — never via the public registration endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.models.schemas import Token, UserCreate, UserLogin, UserOut, UserRole
from app.services.user_store import get_user_store

router = APIRouter()


def _issue_token(user: UserOut) -> Token:
    settings = get_settings()
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return Token(
        access_token=access_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate) -> Token:
    store = get_user_store()
    if store.username_exists(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username is already taken. Please choose another.",
        )
    user = store.create_user(
        username=payload.username,
        password=payload.password,
        full_name=payload.full_name,
        role=UserRole.USER,
    )
    return _issue_token(user)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin) -> Token:
    store = get_user_store()
    user = store.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    return current_user
