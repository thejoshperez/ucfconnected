from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from db.models import Follow, User
from models.schemas import FollowResponse, Token, UserCreate, UserLogin, UserSettingsUpdate
from utils.email_service import EmailDeliveryError, send_verification_email

logger = logging.getLogger(__name__)
settings = get_settings()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def resolve_current_user(session: AsyncSession, token: str) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
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
            detail="User not found - token may be stale",
        )
    return user


def ensure_verified_user(current_user: User) -> User:
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not yet verified. Call POST /auth/verify-email with your code.",
        )
    return current_user


async def register_user(session: AsyncSession, body: UserCreate) -> Token:
    existing_username = await session.execute(
        select(User).where(User.username == body.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken",
        )

    existing_email = await session.execute(select(User).where(User.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists",
        )

    code = generate_verification_code()
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        email=body.email,
        email_verified=False,
        verification_code=code,
    )
    session.add(user)
    await session.flush()

    try:
        send_verification_email(user.email, user.username, code)
    except EmailDeliveryError as exc:
        await session.rollback()
        logger.warning(
            "Registration email delivery failed for %s <%s>: %s",
            user.username,
            user.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't send your verification email right now. Please try again in a moment.",
        ) from exc

    await session.commit()
    await session.refresh(user)
    return Token(
        access_token=create_token(user),
        username=user.username,
        email_verified=user.email_verified,
        detail=f"We sent a verification code to {user.email}.",
    )


async def login_user(session: AsyncSession, body: UserLogin) -> Token:
    result = await session.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    logger.info("User logged in: %s (id=%d)", user.username, user.id)
    return Token(
        access_token=create_token(user),
        username=user.username,
        email_verified=user.email_verified,
    )


async def verify_user_email(
    session: AsyncSession,
    current_user: User,
    code: str,
) -> User:
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified",
        )

    if current_user.verification_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found - call POST /auth/resend-verification first",
        )

    if current_user.verification_code != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect verification code",
        )

    current_user.email_verified = True
    current_user.verification_code = None
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    logger.info(
        "Email verified for user %s (id=%d)",
        current_user.username,
        current_user.id,
    )
    return current_user


async def resend_verification_code(
    session: AsyncSession,
    current_user: User,
) -> dict[str, str]:
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified",
        )

    code = generate_verification_code()
    current_user.verification_code = code
    session.add(current_user)

    try:
        send_verification_email(current_user.email, current_user.username, code)
    except EmailDeliveryError as exc:
        await session.rollback()
        logger.warning(
            "Resend verification email failed for %s <%s>: %s",
            current_user.username,
            current_user.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't resend your verification email right now. Please try again in a moment.",
        ) from exc

    await session.commit()
    return {"detail": f"Verification code sent to {current_user.email}."}


async def follow_club(
    session: AsyncSession,
    current_user: User,
    club_username: str,
) -> FollowResponse:
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


async def unfollow_club(
    session: AsyncSession,
    current_user: User,
    club_username: str,
) -> FollowResponse:
    existing = await session.execute(
        select(Follow).where(
            Follow.user_id == current_user.id,
            Follow.club_username == club_username,
        )
    )
    follow = existing.scalar_one_or_none()

    if follow is None:
        return FollowResponse(
            status="not_following",
            club_username=club_username,
            username=current_user.username,
        )

    await session.delete(follow)
    await session.commit()
    logger.info("User %s unfollowed club @%s", current_user.username, club_username)
    return FollowResponse(
        status="unfollowed",
        club_username=club_username,
        username=current_user.username,
    )


async def list_follows(session: AsyncSession, current_user: User) -> list[str]:
    result = await session.execute(
        select(Follow.club_username).where(Follow.user_id == current_user.id)
    )
    return [row[0] for row in result.all()]


async def update_user_settings(
    session: AsyncSession,
    current_user: User,
    body: UserSettingsUpdate,
) -> User:
    if body.auto_invites_enabled is not None:
        current_user.auto_invites_enabled = body.auto_invites_enabled
    if body.notify_squad_on_rsvp is not None:
        current_user.notify_squad_on_rsvp = body.notify_squad_on_rsvp

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
