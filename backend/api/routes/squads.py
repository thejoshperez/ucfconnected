"""
Squads router — create, view, and join squads.
"""
from __future__ import annotations

import logging
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_session
from db.models import Squad, SquadMember
from models.schemas import SquadCreate, SquadMemberCreate, SquadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/squads", tags=["squads"])

INVITE_CODE_LENGTH = 6
_CODE_ALPHABET = string.ascii_uppercase + string.digits  # A-Z 0-9 → 36^6 ≈ 2.2 billion combos


def _generate_invite_code() -> str:
    """Generate a random 6-character uppercase-alphanumeric invite code."""
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))


async def _get_squad_by_code(
    invite_code: str, session: AsyncSession
) -> Squad:
    """Fetch a squad by invite code or raise 404."""
    result = await session.execute(
        select(Squad)
        .where(Squad.invite_code == invite_code.upper())
        .options(selectinload(Squad.members))
    )
    squad = result.scalar_one_or_none()
    if squad is None:
        raise HTTPException(status_code=404, detail="Squad not found")
    return squad


@router.post("", response_model=SquadResponse, status_code=201, summary="Create a squad")
async def create_squad(
    body: SquadCreate,
    session: AsyncSession = Depends(get_session),
) -> Squad:
    """
    Create a new squad with a randomly generated 6-character invite code.
    The creator should then share this code with friends.
    """
    # Generate a unique code (retry on the astronomically unlikely collision)
    for _ in range(5):
        code = _generate_invite_code()
        existing = await session.execute(
            select(Squad).where(Squad.invite_code == code)
        )
        if existing.scalar_one_or_none() is None:
            break
    else:
        raise HTTPException(
            status_code=500,
            detail="Could not generate a unique invite code. Try again.",
        )

    squad = Squad(name=body.name.strip(), invite_code=code)
    session.add(squad)
    await session.commit()
    await session.refresh(squad, attribute_names=["members"])

    logger.info("Created squad %r with code %s", squad.name, squad.invite_code)
    return squad


@router.get(
    "/{invite_code}",
    response_model=SquadResponse,
    summary="Get squad details by invite code",
)
async def get_squad(
    invite_code: str,
    session: AsyncSession = Depends(get_session),
) -> Squad:
    """Look up a squad and its members by the 6-character invite code."""
    return await _get_squad_by_code(invite_code, session)


@router.post(
    "/{invite_code}/join",
    response_model=SquadResponse,
    status_code=201,
    summary="Join a squad",
)
async def join_squad(
    invite_code: str,
    body: SquadMemberCreate,
    session: AsyncSession = Depends(get_session),
) -> Squad:
    """Add a member to an existing squad using its invite code."""
    squad = await _get_squad_by_code(invite_code, session)

    member = SquadMember(
        squad_id=squad.id,
        member_name=body.member_name.strip(),
    )
    session.add(member)
    await session.commit()

    # Re-fetch with members eagerly loaded for the response
    await session.refresh(squad, attribute_names=["members"])
    logger.info("User %r joined squad %r (%s)", member.member_name, squad.name, squad.invite_code)
    return squad
