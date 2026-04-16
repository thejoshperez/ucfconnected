from __future__ import annotations

import logging
import secrets
import string

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Squad, SquadMember, User

logger = logging.getLogger(__name__)

INVITE_CODE_LENGTH = 6
_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _base_squad_query():
    return select(Squad).options(
        selectinload(Squad.members).selectinload(SquadMember.user)
    )


def _generate_invite_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))


async def get_squad_by_code(invite_code: str, session: AsyncSession) -> Squad:
    result = await session.execute(
        _base_squad_query().where(Squad.invite_code == invite_code.upper())
    )
    squad = result.scalar_one_or_none()
    if squad is None:
        raise HTTPException(status_code=404, detail="Squad not found")
    return squad


async def create_squad(session: AsyncSession, body, current_user: User) -> Squad:
    for _ in range(5):
        code = _generate_invite_code()
        existing = await session.execute(select(Squad).where(Squad.invite_code == code))
        if existing.scalar_one_or_none() is None:
            break
    else:
        raise HTTPException(
            status_code=500,
            detail="Could not generate a unique invite code. Try again.",
        )

    squad = Squad(
        name=body.name.strip(),
        invite_code=code,
        owner_user_id=current_user.id,
        is_public=body.is_public,
    )
    session.add(squad)
    await session.flush()

    session.add(
        SquadMember(
            squad_id=squad.id,
            user_id=current_user.id,
            status="approved",
        )
    )
    await session.commit()

    squad = await get_squad_by_code(code, session)
    logger.info(
        "User %s (id=%d) created squad %r with code %s",
        current_user.username, current_user.id, squad.name, squad.invite_code,
    )
    return squad


async def list_public_squads(session: AsyncSession) -> list[Squad]:
    result = await session.execute(
        _base_squad_query()
        .where(Squad.is_public == True)
        .order_by(Squad.created_at.desc())
        .limit(20)
    )
    return list(result.scalars().all())


async def list_user_squads(session: AsyncSession, current_user: User) -> list[Squad]:
    result = await session.execute(
        _base_squad_query()
        .join(SquadMember, Squad.id == SquadMember.squad_id)
        .where(SquadMember.user_id == current_user.id, SquadMember.status == "approved")
        .order_by(Squad.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def join_squad(session: AsyncSession, invite_code: str, current_user: User) -> Squad:
    squad = await get_squad_by_code(invite_code, session)

    member = SquadMember(
        squad_id=squad.id,
        user_id=current_user.id,
        status="approved" if squad.is_public else "pending",
    )
    session.add(member)

    try:
        await session.commit()
        logger.info(
            "User %s (id=%d) joined squad %r (%s)",
            current_user.username, current_user.id, squad.name, squad.invite_code,
        )
    except IntegrityError:
        await session.rollback()
        logger.info(
            "User %s (id=%d) attempted to join squad %r - already a member.",
            current_user.username, current_user.id, squad.name,
        )

    return await get_squad_by_code(invite_code, session)


async def approve_member(
    session: AsyncSession,
    invite_code: str,
    user_id: int,
    current_user: User,
) -> Squad:
    squad = await get_squad_by_code(invite_code, session)
    if squad.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the squad owner can approve members")

    member = next((member for member in squad.members if member.user_id == user_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Member request not found")

    member.status = "approved"
    await session.commit()
    logger.info("Squad %s owner approved user %d", squad.invite_code, user_id)
    return await get_squad_by_code(invite_code, session)


async def delete_squad(session: AsyncSession, invite_code: str, current_user: User) -> None:
    squad = await get_squad_by_code(invite_code, session)
    if squad.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the squad owner can delete a squad")

    await session.delete(squad)
    await session.commit()
    logger.info(
        "User %s (id=%d) deleted squad %r (%s)",
        current_user.username, current_user.id, squad.name, squad.invite_code,
    )
