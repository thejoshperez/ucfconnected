"""
Auth routes — JWT register / login / follow.

Endpoints
---------
POST /auth/register        — create account, return JWT
POST /auth/login           — verify password, return JWT
POST /auth/follow/{club}   — record a club follow (requires JWT)
GET  /auth/follows         — list current user's followed clubs (requires JWT)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from db.database import get_session
from db.models import Follow, User
from models.schemas import FollowResponse, Token, UserCreate, UserLogin

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

# FastAPI will look for `Authorization: Bearer <token>` on protected endpoints.
# auto_error=False means we raise our own HTTPException for better messages.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ── Dependency: decode JWT and return the User row ────────────────────────────

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — include 'Authorization: Bearer <token>' header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub claim")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalid or expired: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found — token may be stale",
        )
    return user


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, session: AsyncSession = Depends(get_session)) -> Token:
    """Create a new user account and return a JWT."""
    existing = await session.execute(
        select(User).where(User.username == body.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken",
        )

    user = User(
        username=body.username,
        password_hash=_hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info("New user registered: %s (id=%d)", user.username, user.id)
    token = _create_token(user.id, user.username)
    return Token(access_token=token, username=user.username)


@router.post("/login", response_model=Token)
async def login(body: UserLogin, session: AsyncSession = Depends(get_session)) -> Token:
    """Verify credentials and return a JWT."""
    result = await session.execute(
        select(User).where(User.username == body.username)
    )
    user = result.scalar_one_or_none()

    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    logger.info("User logged in: %s (id=%d)", user.username, user.id)
    token = _create_token(user.id, user.username)
    return Token(access_token=token, username=user.username)


@router.post("/follow/{club_username}", response_model=FollowResponse)
async def follow_club(
    club_username: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FollowResponse:
    """Record that the current user is following a club. Idempotent."""
    existing = await session.execute(
        select(Follow).where(
            Follow.user_id == current_user.id,
            Follow.club_username == club_username,
        )
    )
    if existing.scalar_one_or_none():
        return FollowResponse(
            status="already_following",
            club_username=club_username,
            username=current_user.username,
        )

    follow = Follow(user_id=current_user.id, club_username=club_username)
    session.add(follow)
    await session.commit()
    logger.info("User %s followed club @%s", current_user.username, club_username)
    return FollowResponse(
        status="followed",
        club_username=club_username,
        username=current_user.username,
    )


@router.get("/follows", response_model=list[str])
async def get_follows(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[str]:
    """Return list of club usernames the current user follows."""
    result = await session.execute(
        select(Follow.club_username).where(Follow.user_id == current_user.id)
    )
    return [row[0] for row in result.all()]
