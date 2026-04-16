"""
Auth routes - JWT register / login / email verification / profile.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import User
from models.schemas import (
    FollowResponse,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
    UserSettingsUpdate,
    VerifyEmailRequest,
)
from services.auth_service import (
    ensure_verified_user,
    follow_club as follow_club_service,
    list_follows,
    login_user,
    register_user,
    resend_verification_code,
    resolve_current_user,
    unfollow_club as unfollow_club_service,
    update_user_settings,
    verify_user_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - include 'Authorization: Bearer <token>' header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await resolve_current_user(session, token)


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    if not token:
        return None
    try:
        return await resolve_current_user(session, token)
    except HTTPException:
        return None


async def require_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return ensure_verified_user(current_user)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, session: AsyncSession = Depends(get_session)) -> Token:
    return await register_user(session, body)


@router.post("/login", response_model=Token)
async def login(body: UserLogin, session: AsyncSession = Depends(get_session)) -> Token:
    return await login_user(session, body)


@router.post("/verify-email", response_model=UserRead)
async def verify_email(
    body: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    return await verify_user_email(session, current_user, body.code)


@router.post("/resend-verification", response_model=dict)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await resend_verification_code(session, current_user)


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.post("/follow/{club_username}", response_model=FollowResponse)
async def follow_club(
    club_username: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FollowResponse:
    return await follow_club_service(session, current_user, club_username)


@router.delete("/follow/{club_username}", response_model=FollowResponse)
async def unfollow_club(
    club_username: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FollowResponse:
    return await unfollow_club_service(session, current_user, club_username)


@router.get("/follows", response_model=list[str])
async def get_follows(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[str]:
    return await list_follows(session, current_user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    return await update_user_settings(session, current_user, body)
